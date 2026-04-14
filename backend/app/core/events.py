from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.entities import DomainEventRecord


@dataclass(slots=True)
class DomainEvent:
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict
    trace_id: str = field(default_factory=lambda: uuid4().hex)
    event_id: str = field(default_factory=lambda: uuid4().hex)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class EventPublisher:
    def __init__(self, db: Session):
        self.db = db

    def publish(self, event: DomainEvent) -> None:
        record = DomainEventRecord(
            event_id=event.event_id,
            event_type=event.event_type,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            payload=event.payload,
            trace_id=event.trace_id,
            occurred_at=event.occurred_at,
        )
        self.db.add(record)

