from sqlalchemy.orm import Session

from app.models.entities import ChatMessage, ChatSession, Notification, NotificationRead


class InteractionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_session(self, session: ChatSession) -> ChatSession:
        self.db.add(session)
        self.db.flush()
        return session

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

    def create_notification(self, notification: Notification) -> Notification:
        self.db.add(notification)
        self.db.flush()
        return notification

    def list_notifications(self, user_id: int) -> list[Notification]:
        return self.db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    def list_notification_reads(self, user_id: int) -> list[NotificationRead]:
        return self.db.query(NotificationRead).filter_by(user_id=user_id).all()

    def count_unread_notifications(self, user_id: int) -> int:
        total = self.db.query(Notification).filter_by(user_id=user_id).count()
        read = self.db.query(NotificationRead).filter_by(user_id=user_id).count()
        return max(total - read, 0)

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
