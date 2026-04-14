from enum import StrEnum


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"


class ProductStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    OFF_SHELF = "OFF_SHELF"
    BLOCKED = "BLOCKED"


class AuditStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


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


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

