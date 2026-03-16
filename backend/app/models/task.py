from sqlalchemy import Column, String, Text, Enum, Float, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from ..database import Base
import enum

class TaskStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"
    discarded = "discarded"
    pushed = "pushed"

class Priority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(UUID(as_uuid=True), ForeignKey("meetings.id"))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Enum(Priority), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending_review)
    confidence_score = Column(Float, nullable=False)
    assignee_name = Column(String(255), nullable=True)
    source_quote = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
