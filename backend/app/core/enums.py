from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class PresenceStatus(StrEnum):
    ONLINE = "ONLINE"
    INVISIBLE = "INVISIBLE"
    OFFLINE = "OFFLINE"


class ProductStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    OFF_SHELF = "OFF_SHELF"
    BLOCKED = "BLOCKED"
    NEEDS_REVISION = "NEEDS_REVISION"


class AuditStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


class AuditDecision(StrEnum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_CHANGES = "REQUEST_CHANGES"


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class ReportStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSED = "PROCESSED"


class AppealStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class MessageStatus(StrEnum):
    SENT = "SENT"
    READ = "READ"


class ReviewType(StrEnum):
    PRODUCT = "PRODUCT"
    SELLER = "SELLER"


class NotificationTargetScope(StrEnum):
    ALL = "ALL"
    USER = "USER"


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
