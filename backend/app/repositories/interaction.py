from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.entities import AdminNotificationBroadcast, ChatMessage, ChatSession, Notification, NotificationRead, User


class InteractionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session: ChatSession) -> ChatSession:
        self.db.add(session)
        self.db.flush()
        return session

    def find_session(self, buyer_id: int, seller_id: int, product_id: int | None = None) -> ChatSession | None:
        query = self.db.query(ChatSession).filter(
            ChatSession.buyer_id == buyer_id,
            ChatSession.seller_id == seller_id,
        )
        if product_id is None:
            query = query.filter(ChatSession.product_id.is_(None))
        else:
            query = query.filter(ChatSession.product_id == product_id)
        return query.order_by(ChatSession.updated_at.desc(), ChatSession.created_at.desc()).first()

    def list_sessions(self, user_id: int) -> list[ChatSession]:
        return self.db.query(ChatSession).filter((ChatSession.buyer_id == user_id) | (ChatSession.seller_id == user_id)).order_by(ChatSession.updated_at.desc()).all()

    def get_session(self, session_id: int) -> ChatSession | None:
        return self.db.get(ChatSession, session_id)

    def create_message(self, message: ChatMessage) -> ChatMessage:
        self.db.add(message)
        self.db.flush()
        return message

    def list_messages(self, session_id: int) -> list[ChatMessage]:
        return self.db.query(ChatMessage).filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()

    def count_messages(self, session_id: int) -> int:
        return self.db.query(func.count(ChatMessage.id)).filter_by(session_id=session_id).scalar() or 0

    def create_notification(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def create_admin_broadcast(self, notification: AdminNotificationBroadcast) -> AdminNotificationBroadcast:
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_admin_broadcasts(self, limit: int = 20) -> list[AdminNotificationBroadcast]:
        return (
            self.db.query(AdminNotificationBroadcast)
            .order_by(AdminNotificationBroadcast.created_at.desc())
            .limit(limit)
            .all()
        )

    def list_notifications(self, user_id: int) -> list[Notification]:
        return self.db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    def list_notification_reads(self, user_id: int) -> list[NotificationRead]:
        return self.db.query(NotificationRead).filter_by(user_id=user_id).all()

    def count_unread_notifications(self, user_id: int) -> int:
        total = self.db.query(Notification).filter_by(user_id=user_id).count()
        read = self.db.query(NotificationRead).filter_by(user_id=user_id).count()
        return max(total - read, 0)

    def count_unread_notifications_by_target(self, user_id: int, action_target: str) -> int:
        read_subquery = self.db.query(NotificationRead.notification_id).filter_by(user_id=user_id).subquery()
        return (
            self.db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.action_target == action_target,
                ~Notification.id.in_(read_subquery),
            )
            .scalar()
            or 0
        )

    def mark_notification_read(self, user_id: int, notification_id: int) -> NotificationRead:
        existing = (
            self.db.query(NotificationRead)
            .filter_by(user_id=user_id, notification_id=notification_id)
            .first()
        )
        if existing:
            return existing
        read = NotificationRead(user_id=user_id, notification_id=notification_id)
        self.db.add(read)
        self.db.flush()
        return read

    def get_user(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def list_user_ids(self) -> list[int]:
        return [item[0] for item in self.db.query(User.id).all()]
