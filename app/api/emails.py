import secrets
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.models import Email, EmailEvent
from app.schemas import (
    EmailSendRequest,
    EmailSendResponse,
    EmailStatusResponse,
    EmailListResponse,
    EmailEvent as EmailEventSchema,
)
from app.middleware.auth import get_api_key
from app.queue.publisher import publish_email

router = APIRouter()


def generate_message_id() -> str:
    return f"msg_{secrets.token_hex(8)}"


@router.post("/emails", response_model=EmailSendResponse, status_code=202)
async def send_email(
    request: EmailSendRequest,
    api_key=Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Queue an email for delivery."""
    if not request.body_html and not request.body_text:
        raise HTTPException(
            status_code=400,
            detail="At least one of body_html or body_text is required"
        )

    message_id = generate_message_id()
    now = datetime.utcnow()

    email = Email(
        message_id=message_id,
        api_key_id=api_key.id,
        to_email=request.to,
        from_email=request.from_email,
        from_name=request.from_name,
        subject=request.subject,
        body_html=request.body_html,
        body_text=request.body_text,
        reply_to=request.reply_to,
        metadata=request.metadata or {},
        tags=request.tags or [],
        status="queued",
        created_at=now,
        queued_at=now,
    )

    event = EmailEvent(
        email=email,
        event_type="created",
        details={"source": "api"},
        created_at=now,
    )

    db.add(email)
    db.add(event)
    await db.commit()
    await db.refresh(email)

    await publish_email(str(email.id), message_id)

    queued_event = EmailEvent(
        email_id=email.id,
        event_type="queued",
        created_at=datetime.utcnow(),
    )
    db.add(queued_event)
    await db.commit()

    return EmailSendResponse(
        message_id=message_id,
        status="queued",
        created_at=email.created_at,
    )


@router.get("/emails/{message_id}", response_model=EmailStatusResponse)
async def get_email_status(
    message_id: str,
    api_key=Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """Get email delivery status."""
    result = await db.execute(
        select(Email)
        .options(selectinload(Email.events))
        .where(Email.message_id == message_id)
        .where(Email.api_key_id == api_key.id)
    )
    email = result.scalar_one_or_none()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    events = [
        EmailEventSchema(
            event_type=e.event_type,
            provider=e.provider,
            details=e.details,
            created_at=e.created_at,
        )
        for e in sorted(email.events, key=lambda x: x.created_at)
    ]

    return EmailStatusResponse(
        message_id=email.message_id,
        to=email.to_email,
        from_email=email.from_email,
        subject=email.subject,
        status=email.status,
        attempts=email.attempts,
        created_at=email.created_at,
        queued_at=email.queued_at,
        sent_at=email.sent_at,
        delivered_at=email.delivered_at,
        failed_at=email.failed_at,
        last_error=email.last_error,
        events=events,
    )


@router.get("/emails", response_model=EmailListResponse)
async def list_emails(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Results per page"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    api_key=Depends(get_api_key),
    db: AsyncSession = Depends(get_db),
):
    """List emails with pagination and optional status filter."""
    query = select(Email).where(Email.api_key_id == api_key.id)
    count_query = select(func.count(Email.id)).where(Email.api_key_id == api_key.id)

    if status:
        query = query.where(Email.status == status)
        count_query = count_query.where(Email.status == status)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Email.created_at.desc()).offset(offset).limit(limit)
    query = query.options(selectinload(Email.events))

    result = await db.execute(query)
    emails = result.scalars().all()

    email_responses = []
    for email in emails:
        events = [
            EmailEventSchema(
                event_type=e.event_type,
                provider=e.provider,
                details=e.details,
                created_at=e.created_at,
            )
            for e in sorted(email.events, key=lambda x: x.created_at)
        ]
        email_responses.append(
            EmailStatusResponse(
                message_id=email.message_id,
                to=email.to_email,
                from_email=email.from_email,
                subject=email.subject,
                status=email.status,
                attempts=email.attempts,
                created_at=email.created_at,
                queued_at=email.queued_at,
                sent_at=email.sent_at,
                last_error=email.last_error,
                events=events,
            )
        )

    return EmailListResponse(
        emails=email_responses,
        total=total,
        limit=limit,
        offset=offset,
    )
