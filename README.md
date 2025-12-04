# Email Delivery Service

A transactional email API built with FastAPI, RabbitMQ, and PostgreSQL.

This project demonstrates async message processing, reliable delivery, rate limiting, and event-driven architecture patterns.

## Features

- REST API for sending transactional emails
- Async processing via RabbitMQ
- PostgreSQL for storage and event tracking
- Rate limiting per API key (Redis)
- Retry logic with exponential backoff
- Dead letter queue for failed messages

## Quick Start

### Prerequisites

- Docker & Docker Compose
- [Mailtrap account](https://mailtrap.io/) (free tier works)

### 1. Clone and configure

```bash
cd email-service-mvp
cp .env.example .env
```

Edit `.env` with your Mailtrap credentials:
```env
SMTP_USER=your_mailtrap_username
SMTP_PASS=your_mailtrap_password
```

### 2. Start services

```bash
docker-compose up -d
```

This starts:
- API at http://localhost:8000
- PostgreSQL at localhost:5432
- RabbitMQ at localhost:5672 (management UI at http://localhost:15672)
- Redis at localhost:6379
- Worker process for background email processing

### 3. Test the API

```bash
# Health check
curl http://localhost:8000/health

# Send an email
curl -X POST http://localhost:8000/v1/emails \
  -H "X-API-Key: sk_test_demo123456789" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@example.com",
    "from_email": "hello@myapp.com",
    "subject": "Hello from Email Service!",
    "body_text": "This is a test email."
  }'

# Check status
curl http://localhost:8000/v1/emails/msg_XXXXX \
  -H "X-API-Key: sk_test_demo123456789"
```

### 4. View docs

Interactive API documentation: http://localhost:8000/docs

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│  RabbitMQ   │────▶│   Worker    │
│             │     │   (API)     │     │   (Queue)   │     │ (Consumer)  │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                       │
                           ▼                                       ▼
                    ┌─────────────┐                         ┌─────────────┐
                    │ PostgreSQL  │◀────────────────────────│    SMTP     │
                    │             │    status updates       │  (Mailtrap) │
                    └─────────────┘                         └─────────────┘
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/v1/emails` | Send an email |
| `GET` | `/v1/emails/{message_id}` | Get email status |
| `GET` | `/v1/emails` | List emails |

## Project Structure

```
email-service-mvp/
├── app/
│   ├── api/              # API endpoints
│   │   ├── emails.py     # Email CRUD operations
│   │   └── health.py     # Health checks
│   ├── db/
│   │   └── database.py   # Database connection
│   ├── middleware/
│   │   ├── auth.py       # API key authentication
│   │   └── rate_limit.py # Redis rate limiting
│   ├── queue/
│   │   └── publisher.py  # RabbitMQ publisher
│   ├── worker/
│   │   ├── consumer.py   # Message consumer
│   │   └── smtp_sender.py# SMTP client
│   ├── config.py         # Settings
│   ├── models.py         # SQLAlchemy models
│   ├── schemas.py        # Pydantic schemas
│   └── main.py           # FastAPI app
├── scripts/
│   └── init.sql          # Database schema
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Development

### Run locally (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Start dependencies
docker-compose up -d postgres rabbitmq redis

# Run API
uvicorn app.main:app --reload

# Run worker (separate terminal)
python -m app.worker.consumer
```

### Run tests

```bash
pytest tests/ -v
```

## Configuration

All configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/emailservice` |
| `RABBITMQ_URL` | RabbitMQ connection string | `amqp://guest:guest@localhost:5672/` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `SMTP_HOST` | SMTP server hostname | `sandbox.smtp.mailtrap.io` |
| `SMTP_PORT` | SMTP server port | `587` |
| `SMTP_USER` | SMTP username | |
| `SMTP_PASS` | SMTP password | |

## License

MIT
