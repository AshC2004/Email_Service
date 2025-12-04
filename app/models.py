import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime,
    ForeignKey, JSON, ARRAY, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_prefix = Column(String(12), nullable=False)
    key_hash = Column(String(64), nullable=False)
    name = Column(String(255), nullable=False)
    rate_limit_per_minute = Column(Integer, default=60)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)

    emails = relationship("Email", back_populates="api_key")


class Email(Base):
    __tablename__ = "emails"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(String(32), unique=True, nullable=False, index=True)
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"))

    to_email = Column(String(255), nullable=False)
    from_email = Column(String(255), nullable=False)
    from_name = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)
    reply_to = Column(String(255), nullable=True)

    status = Column(String(20), default="queued", index=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)

    metadata = Column(JSON, default=dict)
    tags = Column(ARRAY(String), default=list)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    queued_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    api_key = relationship("APIKey", back_populates="emails")
    events = relationship("EmailEvent", back_populates="email", cascade="all, delete-orphan")


class EmailEvent(Base):
    __tablename__ = "email_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id", ondelete="CASCADE"))
    event_type = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    email = relationship("Email", back_populates="events")
