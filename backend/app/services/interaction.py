from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.events import DomainEvent, EventPublisher
from app.core.realtime import manager
from app.models.entities import ChatMessage, ChatSession, Notification
from app.repositories.interaction import InteractionRepository
from app.schemas.chat import ChatSessionCreateRequest


class InteractionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = InteractionRepository(db)
        self.publisher = EventPublisher(db)

    def create_session(self, buyer_id: int, payload: ChatSessionCreateRequest):
        session = ChatSession(product_id=payload.product_id, buyer_id=buyer_id, seller_id=payload.seller_id)
        self.repo.create_session(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self, user_id: int):
        return self.repo.list_sessions(user_id)

    def list_messages(self, session_id: int, user_id: int):
        session = self.repo.get_session(session_id)
        if not session or user_id not in {session.buyer_id, session.seller_id}:
            raise AppError("Session not found", status_code=404)
        return self.repo.list_messages(session_id)

    async def send_message(self, session_id: int, user_id: int, content: str):
        session = self.repo.get_session(session_id)
        if not session or user_id not in {session.buyer_id, session.seller_id}:
            raise AppError("Session not found", status_code=404)
        message = ChatMessage(session_id=session_id, sender_id=user_id, content=content)
        self.repo.create_message(message)
        recipient_id = session.seller_id if user_id == session.buyer_id else session.buyer_id
        notification = Notification(
            user_id=recipient_id,
            event_type="MESSAGE",
            title="New chat message",
            content=content[:100],
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
        await manager.push(recipient_id, "notification.created", {"title": notification.title, "content": notification.content})
        self.db.refresh(message)
        return message

    def list_notifications(self, user_id: int):
        notifications = self.repo.list_notifications(user_id)
        read_ids = {item.notification_id for item in self.repo.list_notification_reads(user_id)}
        return [
            {
                "id": item.id,
                "event_type": item.event_type,
                "title": item.title,
                "content": item.content,
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
