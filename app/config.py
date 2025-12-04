from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Email Delivery Service"
    debug: bool = False
    api_key_salt: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/emailservice"

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    email_queue_name: str = "email_queue"
    dead_letter_queue: str = "email_dlq"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # SMTP
    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    smtp_use_tls: bool = True

    # Worker
    worker_concurrency: int = 4
    max_retry_attempts: int = 3
    retry_base_delay: int = 5

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
