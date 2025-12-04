import json
import aio_pika
from aio_pika import Message, DeliveryMode

from app.config import get_settings

settings = get_settings()

_connection = None
_channel = None


async def init_rabbitmq():
    global _connection, _channel

    _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    _channel = await _connection.channel()

    await _channel.declare_queue(
        settings.email_queue_name,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": settings.dead_letter_queue,
        }
    )

    await _channel.declare_queue(
        settings.dead_letter_queue,
        durable=True,
    )


async def close_rabbitmq():
    global _connection, _channel

    if _channel:
        await _channel.close()
        _channel = None

    if _connection:
        await _connection.close()
        _connection = None


async def get_connection():
    return _connection


async def publish_email(email_id: str, message_id: str):
    global _channel

    if not _channel:
        raise RuntimeError("RabbitMQ not initialized")

    message_body = json.dumps({
        "email_id": email_id,
        "message_id": message_id,
    })

    message = Message(
        body=message_body.encode(),
        delivery_mode=DeliveryMode.PERSISTENT,
        content_type="application/json",
    )

    await _channel.default_exchange.publish(
        message,
        routing_key=settings.email_queue_name,
    )
