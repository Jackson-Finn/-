from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.enums import NotificationTargetScope, PresenceStatus
from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
from app.core.realtime import manager
from app.models.entities import AdminNotificationBroadcast, ChatMessage, ChatSession, Notification
from app.repositories.catalog import CatalogRepository
from app.repositories.interaction import InteractionRepository
from app.schemas.chat import ChatSessionCreateRequest
from app.schemas.notification import AdminNotificationCreateRequest


class InteractionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InteractionRepository(db)
        self.catalog_repo = CatalogRepository(db)
        self.publisher = EventPublisher(db)

    def create_session(self, buyer_id: int, payload: ChatSessionCreateRequest):
        existing = self.repo.find_session(buyer_id=buyer_id, seller_id=payload.seller_id, product_id=payload.product_id)
        if existing:
            return existing
        session = ChatSession(product_id=payload.product_id, buyer_id=buyer_id, seller_id=payload.seller_id)
        self.repo.create_session(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self, user_id: int):
        return [self.serialize_session(session, user_id) for session in self.repo.list_sessions(user_id)]

    def list_messages(self, session_id: int, user_id: int):
        session = self.repo.get_session(session_id)
        if not session or user_id not in {session.buyer_id, session.seller_id}:
            raise AppError("Session not found", status_code=404)
        return [self.serialize_message(message) for message in self.repo.list_messages(session_id)]

    async def send_message(self, session_id: int, user_id: int, content: str):
        session = self.repo.get_session(session_id)
        if not session or user_id not in {session.buyer_id, session.seller_id}:
            raise AppError("Session not found", status_code=404)
        message = ChatMessage(session_id=session_id, sender_id=user_id, content=content)
        self.repo.create_message(message)
        session.updated_at = datetime.now(timezone.utc)
        recipient_id = session.seller_id if user_id == session.buyer_id else session.buyer_id
        notification = Notification(
            user_id=recipient_id,
            event_type="MESSAGE",
            title="New chat message",
            content=content[:100],
            action_target=f"/messages?sessionId={session_id}",
        )
        self.repo.create_notification(notification)
        self.publisher.publish(
            DomainEvent(
                event_type="MessageSent",
                aggregate_type="ChatMessage",
                aggregate_id=str(message.id),
                payload={"session_id": session_id, "sender_id": user_id},
            )
        )
        self.publisher.publish(
            DomainEvent(
                event_type="NotificationCreated",
                aggregate_type="Notification",
                aggregate_id=str(notification.id),
                payload={"notification_id": notification.id, "user_id": recipient_id},
            )
        )
        self.db.commit()
        await manager.push(recipient_id, "chat.message.created", {"session_id": session_id, "content": content})
        await manager.push(
            recipient_id,
            "notification.created",
            {"title": notification.title, "content": notification.content, "action_target": notification.action_target},
        )
        self.db.refresh(message)
        return self.serialize_message(message)

    def update_presence(self, user_id: int, presence_status: str):
        user = self.repo.get_user(user_id)
        if not user:
            raise AppError("User not found", status_code=404)
        if presence_status not in {item.value for item in PresenceStatus}:
            raise AppError("Unsupported presence status", status_code=400)
        user.presence_status = presence_status
        self.db.commit()
        self.db.refresh(user)
        return {"presence_status": user.presence_status}

    async def publish_admin_notification(self, actor_id: int, payload: AdminNotificationCreateRequest):
        if payload.target_scope not in {NotificationTargetScope.ALL.value, NotificationTargetScope.USER.value}:
            raise AppError("Unsupported notification scope", status_code=400)
        broadcast = AdminNotificationBroadcast(
            actor_id=actor_id,
            target_scope=payload.target_scope,
            target_user_id=payload.target_user_id,
            title=payload.title,
            content=payload.content,
            action_target=payload.action_target,
        )
        self.repo.create_admin_broadcast(broadcast)
        recipient_ids = [payload.target_user_id] if payload.target_scope == NotificationTargetScope.USER.value else self.repo.list_user_ids()
        created_notifications: list[Notification] = []
        for recipient_id in recipient_ids:
            notification = Notification(
                user_id=recipient_id,
                event_type="ADMIN_NOTICE",
                title=payload.title,
                content=payload.content,
                action_target=payload.action_target,
            )
            self.repo.create_notification(notification)
            created_notifications.append(notification)
            self.publisher.publish(
                DomainEvent(
                    event_type="NotificationCreated",
                    aggregate_type="Notification",
                    aggregate_id=str(notification.id),
                    payload={"notification_id": notification.id, "user_id": recipient_id},
                )
            )
        self.db.commit()
        self.db.refresh(broadcast)
        for notification in created_notifications:
            await manager.push(
                notification.user_id,
                "notification.created",
                {"title": notification.title, "content": notification.content, "action_target": notification.action_target},
            )
        return self.serialize_admin_broadcast(broadcast)

    def list_admin_broadcasts(self):
        return [self.serialize_admin_broadcast(item) for item in self.repo.list_admin_broadcasts()]

    def list_notifications(self, user_id: int):
        notifications = self.repo.list_notifications(user_id)
        read_ids = {item.notification_id for item in self.repo.list_notification_reads(user_id)}
        return [
            {
                "id": item.id,
                "event_type": item.event_type,
                "title": item.title,
                "content": item.content,
                "action_target": item.action_target,
                "created_at": item.created_at,
                "read": item.id in read_ids,
            }
            for item in notifications
        ]

    async def mark_notification_read(self, user_id: int, notification_id: int):
        read = self.repo.mark_notification_read(user_id, notification_id)
        self.db.commit()
        unread = self.repo.count_unread_notifications(user_id)
        await manager.push(user_id, "notification.unread.changed", {"unread": unread})
        return read

    def serialize_session(self, session: ChatSession, user_id: int) -> dict:
        counterpart_id = session.seller_id if user_id == session.buyer_id else session.buyer_id
        counterpart = self.repo.get_user(counterpart_id)
        messages = self.repo.list_messages(session.id)
        last_message = messages[-1] if messages else None
        action_target = f"/messages?sessionId={session.id}"
        return {
            "id": session.id,
            "product_id": session.product_id,
            "buyer_id": session.buyer_id,
            "seller_id": session.seller_id,
            "product_summary": self._product_summary(session.product_id),
            "counterpart_name": counterpart.display_name if counterpart else "对方用户",
            "counterpart_presence_status": self._public_presence_status(counterpart) if counterpart else PresenceStatus.OFFLINE.value,
            "last_message_preview": (last_message.content[:100] if last_message else ""),
            "last_message_at": last_message.created_at.isoformat() if last_message and last_message.created_at else None,
            "unread_count": self.repo.count_unread_notifications_by_target(user_id, action_target),
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }

    def serialize_message(self, message: ChatMessage) -> dict:
        sender = self.repo.get_user(message.sender_id)
        return {
            "id": message.id,
            "session_id": message.session_id,
            "sender_id": message.sender_id,
            "sender_name": sender.display_name if sender else None,
            "content": message.content,
            "status": message.status,
            "created_at": message.created_at,
            "updated_at": message.updated_at,
        }

    @staticmethod
    def serialize_admin_broadcast(broadcast: AdminNotificationBroadcast) -> dict:
        return {
            "id": broadcast.id,
            "actor_id": broadcast.actor_id,
            "target_scope": broadcast.target_scope,
            "target_user_id": broadcast.target_user_id,
            "title": broadcast.title,
            "content": broadcast.content,
            "action_target": broadcast.action_target,
            "created_at": broadcast.created_at,
            "updated_at": broadcast.updated_at,
        }

    def _product_summary(self, product_id: int | None) -> dict | None:
        if not product_id:
            return None
        product = self.catalog_repo.get_product(product_id)
        if not product:
            return None
        seller = self.catalog_repo.get_user(product.seller_id)
        category = self.catalog_repo.get_category(product.category_id)
        images = self.catalog_repo.list_product_images(product.id)
        tags = product.tags if isinstance(product.tags, dict) else {}
        detail_sections = tags.get("detail_sections") if isinstance(tags.get("detail_sections"), list) else []
        first_section = detail_sections[0]["body"] if detail_sections and isinstance(detail_sections[0], dict) else product.description
        return {
            "id": product.id,
            "seller_id": product.seller_id,
            "seller_name": seller.display_name if seller else None,
            "category_name": category.name if category else None,
            "title": product.title,
            "price": product.price,
            "product_status": product.product_status,
            "audit_status": product.audit_status,
            "cover_image": images[0].url if images else None,
            "hero_summary": str(tags.get("hero_summary") or first_section[:88]),
            "condition_label": str(tags.get("condition_label") or tags.get("condition") or "成色良好"),
            "updated_at": product.updated_at,
        }

    @staticmethod
    def _public_presence_status(user) -> str:
        if not user or user.presence_status != PresenceStatus.ONLINE.value:
            return PresenceStatus.OFFLINE.value
        return PresenceStatus.ONLINE.value if manager.is_connected(user.id) else PresenceStatus.OFFLINE.value
