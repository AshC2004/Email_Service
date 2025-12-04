import asyncio
import json
import logging
from datetime import datetime

import aio_pika
from aio_pika import IncomingMessage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from app.config import get_settings
from app.models import Email, EmailEvent
from app.worker.smtp_sender import send_email_smtp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()


class EmailWorker:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.queue = None
        self.engine = None
        self.session_factory = None

    async def setup(self):
        """Initialize connections to RabbitMQ and database."""
        database_url = settings.database_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        self.engine = create_async_engine(database_url, echo=False)
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        self.connection = await aio_pika.connect_robust(settings.rabbitmq_url)
        self.channel = await self.connection.channel()

        await self.channel.set_qos(prefetch_count=settings.worker_concurrency)

        self.queue = await self.channel.declare_queue(
            settings.email_queue_name,
            durable=True,
        )

        logger.info("Worker setup complete")

    async def process_message(self, message: IncomingMessage):
        async with message.process():
            try:
                data = json.loads(message.body.decode())
                email_id = data["email_id"]
                message_id = data["message_id"]

                logger.info(f"Processing email {message_id}")

                async with self.session_factory() as session:
                    await self._send_email(session, email_id, message_id)

            except Exception as e:
                logger.error(f"Error processing message: {e}")

    async def _send_email(self, session: AsyncSession, email_id: str, message_id: str):
        result = await session.execute(
            select(Email).where(Email.id == email_id)
        )
        email = result.scalar_one_or_none()

        if not email:
            logger.error(f"Email {email_id} not found")
            return

        if email.status in ("sent", "delivered"):
            logger.info(f"Email {message_id} already sent, skipping")
            return

        if email.attempts >= email.max_attempts:
            await self._mark_failed(session, email, "Max retry attempts exceeded")
            return

        email.status = "sending"
        email.attempts += 1

        attempt_event = EmailEvent(
            email_id=email.id,
            event_type="attempt",
            details={"attempt": email.attempts},
            created_at=datetime.utcnow(),
        )
        session.add(attempt_event)
        await session.commit()

        try:
            await send_email_smtp(
                to_email=email.to_email,
                from_email=email.from_email,
                from_name=email.from_name,
                subject=email.subject,
                body_html=email.body_html,
                body_text=email.body_text,
                reply_to=email.reply_to,
            )

            email.status = "sent"
            email.sent_at = datetime.utcnow()

            sent_event = EmailEvent(
                email_id=email.id,
                event_type="sent",
                provider="smtp",
                details={"smtp_host": settings.smtp_host},
                created_at=datetime.utcnow(),
            )
            session.add(sent_event)
            await session.commit()

            logger.info(f"Email {message_id} sent successfully")

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send {message_id}: {error_msg}")

            fail_event = EmailEvent(
                email_id=email.id,
                event_type="attempt_failed",
                details={"error": error_msg, "attempt": email.attempts},
                created_at=datetime.utcnow(),
            )
            session.add(fail_event)
            email.last_error = error_msg

            if email.attempts < email.max_attempts:
                email.status = "queued"
                await session.commit()

                # TODO: use proper delayed message queue instead of sleep
                delay = settings.retry_base_delay * (2 ** (email.attempts - 1))
                logger.info(f"Scheduling retry for {message_id} in {delay}s")
                await asyncio.sleep(delay)
            else:
                await self._mark_failed(session, email, error_msg)

    async def _mark_failed(self, session: AsyncSession, email: Email, error: str):
        email.status = "failed"
        email.failed_at = datetime.utcnow()
        email.last_error = error

        failed_event = EmailEvent(
            email_id=email.id,
            event_type="failed",
            details={"error": error, "attempts": email.attempts},
            created_at=datetime.utcnow(),
        )
        session.add(failed_event)
        await session.commit()

        logger.warning(f"Email {email.message_id} permanently failed: {error}")

    async def run(self):
        await self.setup()

        logger.info(f"Starting worker, consuming from {settings.email_queue_name}")

        async with self.queue.iterator() as queue_iter:
            async for message in queue_iter:
                await self.process_message(message)

    async def shutdown(self):
        if self.channel:
            await self.channel.close()
        if self.connection:
            await self.connection.close()
        if self.engine:
            await self.engine.dispose()
        logger.info("Worker shutdown complete")


async def main():
    """Main entry point for worker."""
    worker = EmailWorker()
    
    try:
        await worker.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await worker.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
