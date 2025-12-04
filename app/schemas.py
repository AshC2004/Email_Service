from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EmailSendRequest(BaseModel):
    to: EmailStr = Field(..., description="Recipient email address")
    from_email: EmailStr = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, max_length=255, description="Sender display name")
    subject: str = Field(..., min_length=1, max_length=500, description="Email subject")
    body_html: Optional[str] = Field(None, description="HTML body content")
    body_text: Optional[str] = Field(None, description="Plain text body content")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to address")
    metadata: Optional[dict] = Field(default_factory=dict, description="Custom metadata")
    tags: Optional[list[str]] = Field(default_factory=list, description="Tags for categorization")

    class Config:
        json_schema_extra = {
            "example": {
                "to": "user@example.com",
                "from_email": "hello@myapp.com",
                "from_name": "My App",
                "subject": "Welcome to our service!",
                "body_html": "<h1>Welcome!</h1><p>Thanks for signing up.</p>",
                "body_text": "Welcome! Thanks for signing up.",
                "metadata": {"user_id": "123", "campaign": "onboarding"},
                "tags": ["welcome", "transactional"]
            }
        }


class EmailListParams(BaseModel):
    status: Optional[str] = Field(None, description="Filter by status")
    limit: int = Field(20, ge=1, le=100, description="Number of results")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class EmailSendResponse(BaseModel):
    message_id: str
    status: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_7x8k2m9p",
                "status": "queued",
                "created_at": "2025-12-04T10:30:00Z"
            }
        }


class EmailEvent(BaseModel):
    event_type: str
    provider: Optional[str] = None
    details: Optional[dict] = None
    created_at: datetime


class EmailStatusResponse(BaseModel):
    message_id: str
    to: str
    from_email: str
    subject: str
    status: str
    attempts: int
    created_at: datetime
    queued_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    last_error: Optional[str] = None
    events: list[EmailEvent] = []

    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_7x8k2m9p",
                "to": "user@example.com",
                "from_email": "hello@myapp.com",
                "subject": "Welcome!",
                "status": "sent",
                "attempts": 1,
                "created_at": "2025-12-04T10:30:00Z",
                "sent_at": "2025-12-04T10:30:02Z",
                "events": [
                    {"event_type": "created", "created_at": "2025-12-04T10:30:00Z"},
                    {"event_type": "queued", "created_at": "2025-12-04T10:30:00Z"},
                    {"event_type": "sent", "provider": "mailtrap", "created_at": "2025-12-04T10:30:02Z"}
                ]
            }
        }


class EmailListResponse(BaseModel):
    emails: list[EmailStatusResponse]
    total: int
    limit: int
    offset: int


class AnalyticsSummary(BaseModel):
    total_sent: int
    total_delivered: int
    total_failed: int
    total_queued: int
    delivery_rate: float
    avg_delivery_time_seconds: Optional[float] = None
    period_start: datetime
    period_end: datetime


class HealthResponse(BaseModel):
    status: str
    database: str
    rabbitmq: str
    redis: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
