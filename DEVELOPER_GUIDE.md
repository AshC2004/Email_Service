# Complete Developer Guide: Building an Email Delivery Service from Scratch

## Table of Contents
1. [Project Overview](#project-overview)
2. [Skills Required & Learning Path](#skills-required--learning-path)
3. [Architecture & Design Decisions](#architecture--design-decisions)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Understanding Each Component](#understanding-each-component)
6. [Beginner's Implementation Path](#beginners-implementation-path)
7. [Testing & Debugging](#testing--debugging)
8. [Scaling & Production Considerations](#scaling--production-considerations)

---

## Project Overview

### What Are We Building?
An email delivery service similar to SendGrid, Mailgun, or Postmark. It's a backend API that allows applications to send transactional emails (password resets, order confirmations, etc.) reliably and at scale.

### Why This Architecture?
Real-world email services need to handle:
- **High volume**: Thousands of emails per second
- **Reliability**: Emails must eventually get sent, even if the SMTP server is temporarily down
- **Tracking**: Know if an email was sent, failed, or bounced
- **Rate limiting**: Prevent abuse and respect email provider limits
- **Async processing**: Don't block the API while sending emails

---

## Skills Required & Learning Path

### 1. **Python Programming (Intermediate Level)**

**What You Need to Know:**
- Functions, classes, and object-oriented programming
- Async/await (asynchronous programming)
- Type hints
- Error handling (try/except)
- Working with dictionaries, lists, and data structures

**Learning Path (3-4 weeks):**
```
Week 1: Python Basics
- Complete: "Python Crash Course" (book) Chapters 1-11
- Practice: 30 problems on LeetCode Easy
- Project: Build a simple TODO list CLI app

Week 2: Object-Oriented Programming
- Learn: Classes, inheritance, decorators
- Resource: Real Python's OOP tutorials
- Project: Build a library management system

Week 3-4: Async Python
- Learn: asyncio, async/await, concurrent programming
- Resource: "Using Asyncio in Python" by Caleb Hattingh
- Project: Build an async web scraper
```

**Key Resources:**
- [Real Python](https://realpython.com) - Async tutorials
- [Python's asyncio documentation](https://docs.python.org/3/library/asyncio.html)
- Practice: Implement async versions of common tasks

---

### 2. **FastAPI (Web Framework)**

**What You Need to Know:**
- HTTP methods (GET, POST, PUT, DELETE)
- Request/response cycle
- Dependency injection
- Pydantic for data validation
- Middleware and routing

**Learning Path (2 weeks):**
```
Week 1: FastAPI Basics
- Official Tutorial: https://fastapi.tiangolo.com/tutorial/
- Build: Simple REST API for a blog
- Topics: Path operations, request bodies, response models

Week 2: Advanced FastAPI
- Middleware, dependencies, background tasks
- Build: User authentication API with JWT
- Topics: Security, validation, error handling
```

**Practice Project:**
Build a simple blog API with:
- User registration/login
- Create/read/update/delete posts
- Comments system

---

### 3. **Database Design with PostgreSQL**

**What You Need to Know:**
- SQL basics (SELECT, INSERT, UPDATE, DELETE)
- Relationships (one-to-many, many-to-many)
- Indexes and why they matter
- Transactions
- SQLAlchemy ORM

**Learning Path (2-3 weeks):**
```
Week 1: SQL Fundamentals
- Resource: Mode Analytics SQL Tutorial
- Practice: SQLZoo interactive exercises
- Learn: JOINs, GROUP BY, subqueries

Week 2: PostgreSQL Specific
- JSON columns, array types
- Indexes and query optimization
- Transactions and ACID properties

Week 3: SQLAlchemy
- ORM basics, models, relationships
- Async SQLAlchemy
- Migrations with Alembic
```

**Why PostgreSQL for This Project?**
- JSON support (perfect for storing email metadata)
- ARRAY columns (for email tags)
- Excellent performance
- ACID compliance (important for tracking email status)

---

### 4. **Message Queues (RabbitMQ)**

**What You Need to Know:**
- Why queues are needed
- Producer/consumer pattern
- Message persistence
- Dead letter queues
- Exchange types

**Learning Path (1-2 weeks):**
```
Week 1: Queue Concepts
- Read: "RabbitMQ in Action" Chapters 1-3
- Understand: Why not just process emails directly?
- Learn: At-least-once delivery, acknowledgments

Week 2: RabbitMQ Hands-on
- Install RabbitMQ locally
- Build: Simple task queue
- Topics: Durable queues, prefetch, retry logic
```

**Why RabbitMQ for This Project?**
- **Decoupling**: API doesn't wait for email to send
- **Reliability**: Messages persist even if server crashes
- **Scalability**: Can add more workers easily
- **Dead Letter Queue**: Handle failures gracefully

**Alternative**: Could use Redis with Celery, AWS SQS, or Kafka

---

### 5. **Redis (Caching & Rate Limiting)**

**What You Need to Know:**
- Key-value storage
- TTL (time to live)
- Atomic operations (INCR)
- Use cases for caching

**Learning Path (1 week):**
```
- Install Redis locally
- Learn: SET, GET, INCR, EXPIRE commands
- Understand: When to use Redis vs PostgreSQL
- Build: Simple rate limiter
- Resource: Redis University (free courses)
```

**Why Redis for This Project?**
- **Speed**: In-memory = microsecond responses
- **Rate Limiting**: INCR operation is atomic (thread-safe)
- **TTL**: Auto-expire keys (perfect for time windows)

---

### 6. **Docker & Docker Compose**

**What You Need to Know:**
- Containers vs virtual machines
- Dockerfile syntax
- docker-compose.yml structure
- Networking between containers
- Volume mounts

**Learning Path (1 week):**
```
- Read: Docker's Getting Started guide
- Practice: Containerize a Python app
- Learn: Multi-container apps with docker-compose
- Understand: Why containers?
```

**Why Docker for This Project?**
- **Consistency**: Works the same on your machine and in production
- **Dependencies**: PostgreSQL, RabbitMQ, Redis all in one command
- **Isolation**: Each service in its own container

---

## Architecture & Design Decisions

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT APP                          │
│                  (Your website/mobile app)                  │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP POST /v1/emails
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FASTAPI SERVER                         │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Rate Limit │─▶│     Auth     │─▶│  Email API   │       │
│  │ Middleware │  │  Middleware  │  │   Handler    │       │
│  └────────────┘  └──────────────┘  └──────┬───────┘       │
│                                            │                 │
│                                            ▼                 │
│                                     ┌──────────────┐        │
│                                     │  Save to DB  │        │
│                                     └──────┬───────┘        │
│                                            │                 │
│                                            ▼                 │
│                                     ┌──────────────┐        │
│                                     │ Publish to   │        │
│                                     │   RabbitMQ   │        │
│                                     └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                                            │
                    ┌───────────────────────┼───────────────────────┐
                    ▼                       ▼                       ▼
            ┌──────────────┐        ┌──────────────┐      ┌──────────────┐
            │   Worker 1   │        │   Worker 2   │      │   Worker N   │
            │              │        │              │      │              │
            │ 1. Get msg   │        │ 1. Get msg   │      │ 1. Get msg   │
            │ 2. Send SMTP │        │ 2. Send SMTP │      │ 2. Send SMTP │
            │ 3. Update DB │        │ 3. Update DB │      │ 3. Update DB │
            └──────┬───────┘        └──────┬───────┘      └──────┬───────┘
                   │                       │                       │
                   └───────────────────────┼───────────────────────┘
                                           ▼
                                  ┌─────────────────┐
                                  │  SMTP Server    │
                                  │  (Mailtrap/     │
                                  │   SendGrid)     │
                                  └─────────────────┘
```

### Why This Architecture?

#### 1. **Async Processing with Message Queue**

**Problem**: What if we send emails directly in the API?
```python
# BAD APPROACH - Synchronous
@app.post("/emails")
def send_email(request):
    email = save_to_db(request)
    smtp.send(email)  # This takes 1-3 seconds!
    return {"status": "sent"}
```

**Issues:**
- API response takes 3 seconds (user waits)
- If SMTP server is down, API returns error
- Can't scale (limited by SMTP rate limits)
- If server crashes mid-send, email is lost

**Our Solution - Queue-based:**
```python
# GOOD APPROACH - Async
@app.post("/emails")
async def send_email(request):
    email = save_to_db(request)
    publish_to_queue(email.id)  # Instant!
    return {"status": "queued"}  # Returns in <100ms
```

**Benefits:**
- API responds instantly
- Emails send in background
- Can retry failures
- Horizontal scaling (add more workers)

---

#### 2. **Database Schema Design**

**Why Three Tables?**

**`api_keys` Table:**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    key_prefix VARCHAR(12),      -- For quick lookup
    key_hash VARCHAR(64),         -- Security: never store raw keys
    rate_limit_per_minute INT,   -- Per-key rate limits
    is_active BOOLEAN
);
```

**Decision**: Why hash API keys?
- **Security**: If database is compromised, keys aren't exposed
- **Best Practice**: Same reason passwords are hashed

**`emails` Table:**
```sql
CREATE TABLE emails (
    id UUID PRIMARY KEY,
    message_id VARCHAR(32) UNIQUE,  -- Public ID (msg_xxx)
    to_email VARCHAR(255),
    subject VARCHAR(500),
    body_html TEXT,
    status VARCHAR(20),             -- queued, sending, sent, failed
    attempts INT DEFAULT 0,         -- Retry tracking
    created_at TIMESTAMP,
    sent_at TIMESTAMP,
    -- ... more fields
);
```

**Decision**: Why separate `id` and `message_id`?
- `id` (UUID): Internal database reference
- `message_id` (msg_xxx): External API identifier
- **Security**: Don't expose sequential IDs or UUIDs to users

**`email_events` Table:**
```sql
CREATE TABLE email_events (
    id BIGSERIAL PRIMARY KEY,
    email_id UUID REFERENCES emails(id),
    event_type VARCHAR(50),    -- created, queued, sent, failed
    details JSON,              -- Flexible metadata
    created_at TIMESTAMP
);
```

**Decision**: Why event sourcing?
- **Debugging**: Full audit trail of what happened
- **Analytics**: Track delivery rates, failure patterns
- **Compliance**: Some industries require this

---

#### 3. **Rate Limiting Strategy**

**Implementation:**
```python
# Sliding window using Redis
async def check_rate_limit(api_key):
    key = f"ratelimit:{api_key[:12]}"
    current = await redis.incr(key)

    if current == 1:
        await redis.expire(key, 60)  # 60-second window

    if current > limit:
        raise RateLimitExceeded()
```

**Why This Approach?**
- **Redis INCR**: Atomic operation (thread-safe)
- **Auto-expire**: No cleanup needed
- **Sliding window**: More accurate than fixed windows
- **Per-key limits**: Different customers, different limits

**Alternative Approaches:**
1. **Token Bucket**: More complex, smoother rate limiting
2. **Fixed Window**: Simpler but has edge cases (burst at window boundary)
3. **Leaky Bucket**: Good for smoothing traffic

---

#### 4. **Retry Logic with Exponential Backoff**

**Implementation:**
```python
# Retry delays: 5s, 10s, 20s
delay = base_delay * (2 ** (attempt - 1))
```

**Why Exponential Backoff?**
- First retry quick (might be transient error)
- Later retries slower (give system time to recover)
- Prevents overwhelming already-struggling systems

**Decision**: Why 3 max attempts?
- **Cost**: SMTP can be expensive
- **Deliverability**: If it fails 3 times, likely a permanent issue
- **UX**: User should know quickly if email won't send

---

### File Structure Explained

```
app/
├── __init__.py              # Makes directory a Python package
├── main.py                  # Entry point - FastAPI app initialization
├── config.py                # Centralized configuration
├── models.py                # Database models (SQLAlchemy)
├── schemas.py               # API request/response models (Pydantic)
│
├── api/                     # API endpoints
│   ├── emails.py            # Email CRUD operations
│   └── health.py            # Health check endpoints
│
├── middleware/              # Request/response interceptors
│   ├── auth.py              # API key authentication
│   └── rate_limit.py        # Rate limiting logic
│
├── db/                      # Database layer
│   └── database.py          # Connection, session management
│
├── queue/                   # Message queue layer
│   └── publisher.py         # Publish messages to RabbitMQ
│
└── worker/                  # Background workers
    ├── consumer.py          # Consume messages from queue
    └── smtp_sender.py       # Actual SMTP sending logic
```

**Why This Structure?**

1. **Separation of Concerns**: Each directory has one job
2. **Testability**: Easy to mock database, queue, SMTP
3. **Scalability**: Workers can run on separate servers
4. **Maintainability**: Know exactly where to find code

---

## Step-by-Step Implementation

### Phase 1: Project Setup (Day 1)

#### Step 1.1: Initialize Project
```bash
# Create project directory
mkdir email-service
cd email-service

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Initialize git
git init
echo "venv/" >> .gitignore
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
```

#### Step 1.2: Install Dependencies
```bash
# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic-settings==2.1.0
aio-pika==9.3.1
redis==5.0.1
aiosmtplib==3.0.1
EOF

pip install -r requirements.txt
```

**Why These Specific Packages?**
- **FastAPI**: Modern, fast, auto-generates docs
- **uvicorn**: ASGI server for async Python
- **SQLAlchemy**: Industry-standard ORM
- **asyncpg**: Fastest PostgreSQL driver for async
- **aio-pika**: Async RabbitMQ client
- **redis**: Simple Redis client
- **aiosmtplib**: Async SMTP client

---

### Phase 2: Database Layer (Day 2-3)

#### Step 2.1: Design Database Models

**Thought Process:**
1. What data do we need to store?
   - API keys (for authentication)
   - Emails (the actual content)
   - Events (what happened to each email)

2. What relationships exist?
   - One API key → Many emails
   - One email → Many events

3. What queries will we run?
   - Find email by message_id (needs index)
   - List emails by status (needs index)
   - Get events for an email (foreign key handles this)

**Implementation (`app/models.py`):**
```python
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_prefix = Column(String(12), nullable=False)
    key_hash = Column(String(64), nullable=False)
    rate_limit_per_minute = Column(Integer, default=60)

    # Relationship: one key has many emails
    emails = relationship("Email", back_populates="api_key")
```

**Key Decisions:**
- **UUID vs Integer ID**: UUIDs don't leak information about volume
- **key_prefix**: Allows fast lookup without comparing full hash
- **rate_limit_per_minute**: Per-customer rate limits

---

#### Step 2.2: Database Connection (`app/db/database.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# Why async engine?
# - Non-blocking I/O
# - Can handle thousands of concurrent requests
# - Essential for async FastAPI

engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/dbname",
    pool_size=10,        # Connection pool
    max_overflow=20      # Extra connections if needed
)
```

**Decision**: Why connection pooling?
- Creating DB connections is expensive (100-200ms)
- Reusing connections is fast (<1ms)
- Pool size depends on expected concurrent requests

---

### Phase 3: API Layer (Day 4-7)

#### Step 3.1: FastAPI Application (`app/main.py`)

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to database, RabbitMQ
    await init_db()
    await init_rabbitmq()
    yield
    # Shutdown: Close connections
    await close_db()
    await close_rabbitmq()

app = FastAPI(lifespan=lifespan)
```

**Why Lifespan Events?**
- **Startup**: Initialize expensive resources once
- **Shutdown**: Clean up connections (prevents resource leaks)
- **Alternative**: Could use `@app.on_event("startup")` but lifespan is newer

---

#### Step 3.2: Request/Response Schemas (`app/schemas.py`)

```python
from pydantic import BaseModel, EmailStr, Field

class EmailSendRequest(BaseModel):
    to: EmailStr                    # Validates email format
    subject: str = Field(min_length=1, max_length=500)
    body_html: str | None = None
    body_text: str | None = None
```

**Why Pydantic?**
- **Auto-validation**: Invalid emails rejected automatically
- **Type safety**: Catches bugs at runtime
- **Auto-documentation**: FastAPI uses this for Swagger docs
- **Serialization**: Converts to/from JSON

**Decision**: Why EmailStr?
- Validates email format (prevents typos)
- Rejects invalid inputs early
- Better UX (clear error messages)

---

#### Step 3.3: Email API Endpoint (`app/api/emails.py`)

```python
@router.post("/emails", response_model=EmailSendResponse, status_code=202)
async def send_email(
    request: EmailSendRequest,
    api_key=Depends(get_api_key),  # Dependency injection
    db: AsyncSession = Depends(get_db)
):
    # 1. Validate request
    if not request.body_html and not request.body_text:
        raise HTTPException(400, "Need at least one body")

    # 2. Generate message ID
    message_id = f"msg_{secrets.token_hex(8)}"

    # 3. Save to database
    email = Email(message_id=message_id, ...)
    db.add(email)
    await db.commit()

    # 4. Publish to queue
    await publish_email(email.id, message_id)

    # 5. Return immediately (don't wait for send)
    return {"message_id": message_id, "status": "queued"}
```

**Key Decisions:**

**1. Why status code 202 (Accepted)?**
- 200 means "done" - but we haven't sent yet
- 202 means "accepted for processing" - accurate
- RESTful best practice for async operations

**2. Why generate `message_id` like `msg_xxx`?**
- User-friendly (easy to reference in support)
- Doesn't expose internal IDs
- Consistent with services like Stripe

**3. Why commit before publishing to queue?**
- If commit fails, don't queue (data consistency)
- If queue fails, can retry (email is in DB)
- Order matters!

---

### Phase 4: Authentication & Security (Day 8-9)

#### Step 4.1: API Key Authentication (`app/middleware/auth.py`)

```python
def hash_api_key(key: str) -> str:
    salted = f"{settings.api_key_salt}{key}"
    return hashlib.sha256(salted.encode()).hexdigest()

async def get_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    # Extract prefix for fast lookup
    key_prefix = api_key[:12]
    key_hash = hash_api_key(api_key)

    # Find in database
    result = await db.execute(
        select(APIKey).where(
            APIKey.key_prefix == key_prefix,
            APIKey.key_hash == key_hash
        )
    )
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        raise HTTPException(401, "Invalid API key")

    return api_key_record
```

**Security Decisions:**

**1. Why hash API keys?**
- **Database breach**: Attackers can't use keys
- **Insider threat**: DBAs can't see keys
- **Compliance**: PCI-DSS, SOC 2 requirements

**2. Why use salt?**
- Prevents rainbow table attacks
- Makes hash unique per installation
- Must be kept secret (in environment variables)

**3. Why prefix + hash lookup?**
- **Performance**: Index on short prefix is fast
- **Security**: Still verify full hash
- **Scalability**: Can shard by prefix later

---

#### Step 4.2: Rate Limiting (`app/middleware/rate_limit.py`)

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        api_key = request.headers.get("X-API-Key")

        key = f"ratelimit:{api_key[:12]}"
        current = await redis.incr(key)

        if current == 1:
            await redis.expire(key, 60)

        if current > limit:
            raise HTTPException(429, "Rate limit exceeded")

        return await call_next(request)
```

**Design Decisions:**

**1. Why middleware instead of decorator?**
- **Centralized**: One place for all rate limiting
- **Global**: Applies to all endpoints automatically
- **Order matters**: Runs before route handlers

**2. Why Redis instead of database?**
- **Speed**: In-memory (sub-millisecond)
- **Atomic**: INCR is thread-safe
- **TTL**: Auto-cleanup
- **Scale**: Can handle millions of ops/second

**3. Why sliding window?**
```
Fixed window problem:
- 10:00:59 - 60 requests
- 10:01:01 - 60 requests
= 120 requests in 2 seconds!

Sliding window:
- Always looks at last 60 seconds
- No burst at boundaries
```

---

### Phase 5: Message Queue (Day 10-11)

#### Step 5.1: RabbitMQ Publisher (`app/queue/publisher.py`)

```python
async def init_rabbitmq():
    global _connection, _channel

    _connection = await aio_pika.connect_robust(rabbitmq_url)
    _channel = await _connection.channel()

    # Declare queue with dead letter exchange
    await _channel.declare_queue(
        "email_queue",
        durable=True,  # Survives RabbitMQ restart
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": "email_dlq"
        }
    )
```

**Key Concepts:**

**1. What is `durable=True`?**
- Queue persists even if RabbitMQ crashes
- Messages written to disk
- Slight performance cost but worth it

**2. What is a Dead Letter Queue (DLQ)?**
```
Normal flow:
API → Queue → Worker → SMTP ✓

Failed flow:
API → Queue → Worker → SMTP ✗ (retry)
              Worker → SMTP ✗ (retry)
              Worker → SMTP ✗ (max retries)
              → DLQ (give up, human review)
```

**3. Why connect_robust?**
- Auto-reconnects if connection drops
- Exponential backoff
- Essential for production

---

#### Step 5.2: Publishing Messages

```python
async def publish_email(email_id: str, message_id: str):
    message_body = json.dumps({
        "email_id": email_id,
        "message_id": message_id
    })

    message = Message(
        body=message_body.encode(),
        delivery_mode=DeliveryMode.PERSISTENT  # Write to disk
    )

    await _channel.default_exchange.publish(
        message,
        routing_key="email_queue"
    )
```

**Decision**: Why PERSISTENT delivery mode?
- Message survives RabbitMQ restart
- Trade-off: Slower (disk I/O) but reliable
- Critical for email delivery (can't lose emails)

---

### Phase 6: Background Workers (Day 12-14)

#### Step 6.1: Worker Architecture (`app/worker/consumer.py`)

```python
class EmailWorker:
    async def process_message(self, message: IncomingMessage):
        async with message.process():  # Auto-ack on success
            try:
                data = json.loads(message.body)
                await self._send_email(data["email_id"])
            except Exception as e:
                logger.error(f"Error: {e}")
                # Message will be nacked and go to DLQ
```

**Key Concepts:**

**1. What is `message.process()`?**
```python
# Without context manager:
try:
    process_message()
    await message.ack()  # Tell RabbitMQ we're done
except:
    await message.nack()  # Tell RabbitMQ we failed

# With context manager (automatic):
async with message.process():
    process_message()  # Auto-ack on success, nack on exception
```

**2. Why async context manager?**
- Guarantees ack/nack even if exception
- Prevents message loss
- Cleaner code

---

#### Step 6.2: Retry Logic

```python
async def _send_email(self, session, email_id, message_id):
    email = await session.get(Email, email_id)

    # Check if already sent
    if email.status in ("sent", "delivered"):
        return

    # Check max attempts
    if email.attempts >= 3:
        await self._mark_failed(session, email)
        return

    # Increment attempts
    email.attempts += 1
    await session.commit()

    try:
        await send_email_smtp(email)
        email.status = "sent"
        email.sent_at = datetime.utcnow()
    except Exception as e:
        email.last_error = str(e)

        if email.attempts < 3:
            # Exponential backoff: 5s, 10s, 20s
            delay = 5 * (2 ** (email.attempts - 1))
            await asyncio.sleep(delay)
            # Re-queue (in production, use RabbitMQ delayed exchange)
        else:
            await self._mark_failed(session, email)
```

**Design Decisions:**

**1. Why check `if already sent`?**
- **Idempotency**: Safe to process same message twice
- **RabbitMQ redelivery**: Can happen on crashes
- **At-least-once delivery**: Better than at-most-once

**2. Why exponential backoff?**
```
Linear backoff (5s, 5s, 5s):
- Doesn't give system time to recover
- Might keep hitting rate limits

Exponential (5s, 10s, 20s):
- First retry quick (might be transient)
- Later retries slower (respect recovery time)
- Industry standard pattern
```

**3. Why store `last_error`?**
- **Debugging**: Know why it failed
- **Analytics**: Common failure patterns
- **User support**: Help customers fix issues

---

#### Step 6.3: SMTP Sending (`app/worker/smtp_sender.py`)

```python
async def send_email_smtp(
    to_email: str,
    subject: str,
    body_html: str | None,
    body_text: str | None,
):
    # Build multipart message
    if body_html and body_text:
        message = MIMEMultipart("alternative")
        message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))
    elif body_html:
        message = MIMEText(body_html, "html")
    else:
        message = MIMEText(body_text, "plain")

    # Send
    await aiosmtplib.send(
        message,
        hostname=smtp_host,
        port=587,
        use_tls=True
    )
```

**Email Concepts:**

**1. What is MIME multipart?**
```
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary"

--boundary
Content-Type: text/plain

This is plain text version

--boundary
Content-Type: text/html

<p>This is <b>HTML</b> version</p>

--boundary--
```

Email clients choose which version to display.

**2. Why send both HTML and text?**
- **Accessibility**: Screen readers prefer plain text
- **Email clients**: Some strip HTML (corporate firewalls)
- **Spam filters**: HTML-only emails flagged more often
- **Best practice**: Always provide fallback

**3. Why TLS?**
- **Security**: Encrypts email in transit
- **Privacy**: ISPs can't read content
- **Required**: Many SMTP servers reject non-TLS

---

### Phase 7: Configuration Management (Day 15)

#### Step 7.1: Settings (`app/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://localhost/emailservice"
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"
    smtp_host: str = "sandbox.smtp.mailtrap.io"
    smtp_user: str = ""
    smtp_pass: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False
```

**Why Pydantic Settings?**
- **Type validation**: `smtp_port: int` ensures it's a number
- **Environment variables**: Auto-loads from .env
- **Defaults**: Fallback values for development
- **Documentation**: Self-documenting code

**Security Best Practices:**
```bash
# .env (NEVER commit this!)
DATABASE_URL=postgresql://user:pass@localhost/db
SMTP_USER=your_username
SMTP_PASS=your_password

# .gitignore
.env
```

---

### Phase 8: Docker Setup (Day 16-17)

#### Step 8.1: Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/

# Run API server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Dockerfile Decisions:**

**1. Why `python:3.11-slim`?**
- **Slim**: Smaller image (200MB vs 1GB)
- **Security**: Fewer packages = smaller attack surface
- **Speed**: Faster builds and deploys

**2. Why copy requirements.txt first?**
```dockerfile
# Bad:
COPY . .
RUN pip install -r requirements.txt
# Every code change = reinstall all packages

# Good:
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ .
# Code changes don't reinstall packages (Docker layer caching)
```

**3. Why `--no-cache-dir`?**
- Saves ~100MB (doesn't keep pip cache)
- Smaller Docker image
- Not needed (never pip install in container again)

---

#### Step 8.2: Docker Compose (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: emailservice
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"      # AMQP
      - "15672:15672"    # Management UI

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --reload
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - rabbitmq
      - redis
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres/emailservice
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
      REDIS_URL: redis://redis:6379/0

  worker:
    build: .
    command: python -m app.worker.consumer
    depends_on:
      - postgres
      - rabbitmq
    environment:
      DATABASE_URL: postgresql://postgres:postgres@postgres/emailservice
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/

volumes:
  postgres_data:
```

**Docker Compose Concepts:**

**1. Why use volumes?**
```yaml
volumes:
  - postgres_data:/var/lib/postgresql/data
```
- **Persistence**: Data survives container restarts
- **Performance**: Native filesystem speed
- **Backup**: Easy to backup/restore

**2. Why `depends_on`?**
- **Start order**: PostgreSQL starts before API
- **Not a health check**: API might start before PostgreSQL is ready
- **Solution**: Add connection retry logic in app

**3. Why separate worker service?**
- **Scaling**: `docker-compose up --scale worker=5`
- **Resources**: Can give workers more CPU/memory
- **Deployment**: Can deploy workers separately

---

## Understanding Each Component

### Component 1: FastAPI Application

**What FastAPI Does:**
1. **Routing**: Maps URLs to Python functions
2. **Validation**: Checks incoming data
3. **Serialization**: Converts Python objects to JSON
4. **Documentation**: Auto-generates Swagger UI
5. **Dependency Injection**: Manages shared resources

**Real-World Example:**
```python
# Without FastAPI (raw HTTP):
def handle_request(raw_request):
    # Parse JSON manually
    data = json.loads(raw_request.body)

    # Validate manually
    if 'email' not in data:
        return error_response(400, "Missing email")
    if not is_valid_email(data['email']):
        return error_response(400, "Invalid email")

    # Process...
    result = process_email(data)

    # Serialize manually
    return json.dumps(result)

# With FastAPI:
@app.post("/emails")
async def send_email(request: EmailRequest):
    # Validation automatic!
    # Serialization automatic!
    return process_email(request)
```

---

### Component 2: SQLAlchemy ORM

**What ORM Does:**
Translates Python code to SQL queries.

**Example:**
```python
# Without ORM (raw SQL):
cursor.execute("""
    SELECT * FROM emails
    WHERE message_id = %s AND api_key_id = %s
""", (message_id, api_key_id))
row = cursor.fetchone()
email = Email(
    id=row[0],
    message_id=row[1],
    to_email=row[2],
    # ... map all 20+ fields manually
)

# With ORM:
email = await session.execute(
    select(Email)
    .where(Email.message_id == message_id)
    .where(Email.api_key_id == api_key_id)
).scalar_one()
# All fields mapped automatically!
```

**Benefits:**
- Type safety (IDE autocomplete)
- Relationships handled automatically
- Database-agnostic (switch PostgreSQL → MySQL easily)

**Trade-offs:**
- Slight performance overhead
- Complex queries harder to optimize
- Learning curve

---

### Component 3: RabbitMQ

**Message Queue Analogy:**
```
Without queue:
Customer → Cashier → Kitchen → Food
(Customer waits 15 minutes)

With queue:
Customer → Cashier → Order # → Leave
           Cashier → Kitchen Queue
           Kitchen → Cooks when ready
(Customer waits 30 seconds for order number)
```

**How RabbitMQ Works:**
```
Producer (API):
    message = {"email_id": "123", "to": "user@example.com"}
    channel.publish(message, queue="emails")

Queue (RabbitMQ):
    [message1, message2, message3, ...]

Consumer (Worker):
    message = channel.consume("emails")
    send_email(message)
    channel.ack(message)  # Remove from queue
```

**Why Not Just Database Queue?**
```python
# Database as queue (bad):
while True:
    emails = db.query("SELECT * FROM emails WHERE status='pending' LIMIT 1")
    for email in emails:
        send_email(email)
        db.query("UPDATE emails SET status='sent' WHERE id=?", email.id)
```

**Problems:**
- **Polling overhead**: Constant DB queries even if empty
- **Race conditions**: Two workers might get same email
- **No distribution**: Can't easily split work across workers
- **Performance**: Database not optimized for queues

**RabbitMQ Solutions:**
- **Push-based**: Workers notified when message arrives
- **Atomic operations**: One message → one worker (guaranteed)
- **Load balancing**: Round-robin across workers
- **Optimized**: Designed specifically for messaging

---

### Component 4: Redis for Rate Limiting

**How Rate Limiting Works:**

**Simple Counter (broken):**
```python
# BAD: Race condition
count = redis.get(f"count:{api_key}")
if count >= 60:
    raise RateLimitError()
redis.set(f"count:{api_key}", count + 1)

# Problem: Two requests at same time
Request A reads count=59
Request B reads count=59
Request A sets count=60
Request B sets count=60 (should be 61!)
```

**Atomic Counter (correct):**
```python
# GOOD: Atomic operation
count = redis.incr(f"count:{api_key}")  # One operation
if count == 1:
    redis.expire(f"count:{api_key}", 60)
if count > 60:
    raise RateLimitError()

# INCR is atomic: Request A and B both increment correctly
```

**Why Redis?**
- **Atomic operations**: INCR, EXPIRE are thread-safe
- **Speed**: Sub-millisecond latency
- **TTL**: Auto-cleanup (no manual deletion needed)
- **Simple**: Easy to understand and debug

---

## Beginner's Implementation Path

### Month 1: Python & Web Basics

**Week 1-2: Python Fundamentals**
```python
# Day 1-3: Variables, functions, loops
def calculate_total(items):
    total = 0
    for item in items:
        total += item['price']
    return total

# Day 4-7: Classes and OOP
class Email:
    def __init__(self, to, subject, body):
        self.to = to
        self.subject = subject
        self.body = body

    def is_valid(self):
        return '@' in self.to

# Day 8-14: File I/O, error handling, modules
try:
    with open('config.json') as f:
        config = json.load(f)
except FileNotFoundError:
    config = default_config()
```

**Practice Projects:**
1. **Week 1**: Build a command-line TODO app
2. **Week 2**: Build a simple blog (file-based storage)

---

**Week 3: Web Concepts**
```python
# Understand HTTP
"""
Request:
POST /api/emails HTTP/1.1
Host: example.com
Content-Type: application/json

{"to": "user@example.com", "subject": "Hi"}

Response:
HTTP/1.1 200 OK
Content-Type: application/json

{"message_id": "msg_123", "status": "sent"}
"""

# Build simple Flask app
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/emails', methods=['POST'])
def send_email():
    data = request.json
    # Validate
    if 'to' not in data:
        return jsonify({"error": "Missing 'to'"}), 400
    # Process
    return jsonify({"message_id": "msg_123"}), 200
```

**Practice Project:** Build a simple REST API for notes (CRUD operations)

---

**Week 4: Async Python**
```python
# Day 1-2: Understand async/await
import asyncio

# Synchronous (blocking)
def fetch_data():
    time.sleep(2)  # Wait 2 seconds
    return "data"

def main():
    data1 = fetch_data()  # Takes 2 seconds
    data2 = fetch_data()  # Takes 2 seconds
    # Total: 4 seconds

# Asynchronous (non-blocking)
async def fetch_data_async():
    await asyncio.sleep(2)
    return "data"

async def main_async():
    data1 = fetch_data_async()  # Start task
    data2 = fetch_data_async()  # Start task
    await asyncio.gather(data1, data2)  # Wait for both
    # Total: 2 seconds (concurrent!)

# Day 3-7: Async HTTP, databases
import aiohttp

async def fetch_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

**Practice Project:** Build async web scraper (fetch 100 URLs concurrently)

---

### Month 2: Databases & APIs

**Week 1-2: SQL & PostgreSQL**
```sql
-- Day 1-3: Basic queries
SELECT * FROM emails WHERE status = 'sent';

INSERT INTO emails (to_email, subject, body)
VALUES ('user@example.com', 'Hi', 'Hello!');

UPDATE emails SET status = 'sent' WHERE id = 1;

-- Day 4-7: Joins and relationships
SELECT emails.*, api_keys.name
FROM emails
JOIN api_keys ON emails.api_key_id = api_keys.id;

-- Day 8-14: Indexes and performance
CREATE INDEX idx_emails_status ON emails(status);
CREATE INDEX idx_emails_created_at ON emails(created_at);

EXPLAIN ANALYZE
SELECT * FROM emails WHERE status = 'sent';
```

**Practice Project:** Design database for a blog (users, posts, comments)

---

**Week 3: SQLAlchemy ORM**
```python
# Define models
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
    posts = relationship("Post", back_populates="author")

class Post(Base):
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    author_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="posts")

# Query
user = session.query(User).filter_by(email='user@example.com').first()
posts = user.posts  # Automatically fetches related posts
```

**Practice Project:** Convert blog from Week 1-2 to use SQLAlchemy

---

**Week 4: FastAPI**
```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()

class PostCreate(BaseModel):
    title: str
    content: str

@app.post("/posts")
async def create_post(
    post: PostCreate,
    db: Session = Depends(get_db)
):
    db_post = Post(title=post.title, content=post.content)
    db.add(db_post)
    db.commit()
    return {"id": db_post.id}
```

**Practice Project:** Build full CRUD API for blog with authentication

---

### Month 3: Message Queues & Background Jobs

**Week 1-2: RabbitMQ Basics**
```python
# Producer (sends messages)
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters('localhost')
)
channel = connection.channel()
channel.queue_declare(queue='tasks')

channel.basic_publish(
    exchange='',
    routing_key='tasks',
    body='Send email to user@example.com'
)

# Consumer (processes messages)
def callback(ch, method, properties, body):
    print(f"Processing: {body}")
    # Do work...
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(
    queue='tasks',
    on_message_callback=callback
)
channel.start_consuming()
```

**Practice Project:** Build a task queue (image processing, send emails, etc.)

---

**Week 3-4: Async RabbitMQ & Integration**
```python
import aio_pika

# In FastAPI endpoint
@app.post("/tasks")
async def create_task(task: TaskCreate):
    # Save to database
    db_task = Task(name=task.name)
    db.add(db_task)
    db.commit()

    # Publish to queue
    await publish_message({
        "task_id": db_task.id,
        "name": task.name
    })

    return {"task_id": db_task.id, "status": "queued"}

# In worker
async def process_task(message):
    data = json.loads(message.body)
    task = db.query(Task).get(data['task_id'])

    # Do work...
    task.status = 'completed'
    db.commit()
```

**Practice Project:** Build a URL shortener with analytics (queue click tracking)

---

### Month 4: Build Email Service

**Week 1: Setup & Core Models**
- Day 1-2: Project setup, Docker Compose
- Day 3-4: Database models (API keys, emails, events)
- Day 5-7: Basic FastAPI endpoints (send email, get status)

**Week 2: Authentication & Queue**
- Day 1-2: API key authentication
- Day 3-4: Rate limiting with Redis
- Day 5-7: RabbitMQ integration (publish messages)

**Week 3: Workers & SMTP**
- Day 1-3: Consumer worker (process queue)
- Day 4-5: SMTP sending logic
- Day 6-7: Retry logic and error handling

**Week 4: Polish & Deploy**
- Day 1-2: Event tracking (created, queued, sent, failed)
- Day 3-4: Health checks, monitoring
- Day 5-7: Documentation, testing, deployment

---

## Testing & Debugging

### Unit Tests

**Test Database Models:**
```python
import pytest
from app.models import Email

def test_email_creation():
    email = Email(
        message_id="msg_test123",
        to_email="user@example.com",
        subject="Test",
        body_text="Hello"
    )
    assert email.message_id == "msg_test123"
    assert email.status == "queued"  # Default status
```

**Test API Endpoints:**
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_send_email():
    response = client.post(
        "/v1/emails",
        headers={"X-API-Key": "sk_test_123"},
        json={
            "to": "user@example.com",
            "from_email": "app@example.com",
            "subject": "Test",
            "body_text": "Hello"
        }
    )
    assert response.status_code == 202
    assert "message_id" in response.json()
```

**Test Rate Limiting:**
```python
def test_rate_limit():
    # Send 61 requests (limit is 60)
    for i in range(61):
        response = client.post("/v1/emails", ...)

        if i < 60:
            assert response.status_code == 202
        else:
            assert response.status_code == 429  # Rate limited
```

---

### Integration Tests

**Test Full Flow:**
```python
@pytest.mark.asyncio
async def test_email_delivery_flow():
    # 1. Send via API
    response = client.post("/v1/emails", json={...})
    message_id = response.json()["message_id"]

    # 2. Wait for worker to process
    await asyncio.sleep(5)

    # 3. Check status
    response = client.get(f"/v1/emails/{message_id}")
    assert response.json()["status"] == "sent"

    # 4. Verify events logged
    events = response.json()["events"]
    assert any(e["event_type"] == "created" for e in events)
    assert any(e["event_type"] == "sent" for e in events)
```

---

### Debugging Techniques

**1. Logging Strategy**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In code
logger.info(f"Processing email {message_id}")
logger.error(f"Failed to send: {error}", exc_info=True)
```

**Log Levels:**
- **DEBUG**: Detailed info for diagnosing problems
- **INFO**: General informational messages
- **WARNING**: Something unexpected but handled
- **ERROR**: Error occurred, function failed
- **CRITICAL**: System-level failure

---

**2. Using Docker Logs**
```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# View specific container
docker logs <container_id> --tail 100 --follow
```

---

**3. Database Debugging**
```python
# Enable SQL echo (see all queries)
engine = create_async_engine(
    database_url,
    echo=True  # Prints all SQL statements
)

# Check what's in database
docker exec -it postgres_container psql -U postgres -d emailservice
SELECT * FROM emails WHERE message_id = 'msg_xxx';
```

---

**4. RabbitMQ Management UI**
```
Open: http://localhost:15672
Username: guest
Password: guest

- See queue depth (messages waiting)
- Monitor message rates
- View dead letter queue
- Manually purge queues
```

---

## Scaling & Production Considerations

### Performance Optimization

**1. Database Connection Pooling**
```python
# Bad: New connection for each request
async def get_db():
    engine = create_async_engine(db_url)  # Expensive!
    async with engine.connect() as conn:
        yield conn

# Good: Reuse connection pool
engine = create_async_engine(
    db_url,
    pool_size=10,          # Keep 10 connections open
    max_overflow=20,       # Allow 20 extra if needed
    pool_pre_ping=True     # Test connections before use
)
```

**Tuning:**
- **pool_size**: Expected concurrent requests ÷ avg query time
- **max_overflow**: Handle traffic spikes
- Too small: Requests wait for connections
- Too large: PostgreSQL overhead (each connection = memory)

---

**2. Database Indexes**
```sql
-- Slow query (full table scan)
SELECT * FROM emails WHERE status = 'sent';
-- Scans 1 million rows: ~500ms

-- Add index
CREATE INDEX idx_emails_status ON emails(status);
-- Now uses index: ~5ms

-- Composite index for common queries
CREATE INDEX idx_emails_api_key_created
ON emails(api_key_id, created_at DESC);

-- Query uses index
SELECT * FROM emails
WHERE api_key_id = '123'
ORDER BY created_at DESC
LIMIT 20;
```

**Index Strategy:**
- Index foreign keys (api_key_id, email_id)
- Index frequently queried columns (status, created_at)
- Composite indexes for common query patterns
- Don't over-index (slows down writes)

---

**3. Caching with Redis**
```python
# Cache API key lookups
async def get_api_key(key: str):
    # Check cache first
    cached = await redis.get(f"apikey:{key[:12]}")
    if cached:
        return json.loads(cached)

    # Not in cache, query database
    api_key = await db.query(APIKey).filter_by(
        key_prefix=key[:12]
    ).first()

    # Cache for 5 minutes
    await redis.setex(
        f"apikey:{key[:12]}",
        300,
        json.dumps(api_key.to_dict())
    )

    return api_key
```

**What to Cache:**
- API key lookups (rarely change)
- Email templates
- Configuration settings

**What NOT to Cache:**
- Email status (changes frequently)
- Event logs (must be real-time)

---

### Horizontal Scaling

**1. Scaling API Servers**
```bash
# Run multiple API instances
docker-compose up --scale api=3

# Add load balancer (nginx)
upstream api_servers {
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

**Considerations:**
- **Stateless**: No session storage in memory
- **Database connections**: Each instance needs pool
- **Health checks**: Load balancer checks /health

---

**2. Scaling Workers**
```bash
# Run 10 workers
docker-compose up --scale worker=10
```

**Benefits:**
- Process emails faster (parallel processing)
- Handle spikes in email volume
- Fault tolerance (if one worker crashes, others continue)

**Limits:**
- **SMTP rate limits**: Sending 1000/second might get blocked
- **Database connections**: Each worker needs connections
- **RabbitMQ**: Set prefetch_count to distribute evenly

---

**3. Database Scaling**

**Read Replicas:**
```python
# Master (writes)
write_engine = create_engine("postgresql://master:5432/db")

# Replica (reads)
read_engine = create_engine("postgresql://replica:5432/db")

# Use read replica for queries
async def get_email_status(message_id):
    async with read_engine.connect() as conn:
        result = await conn.execute(
            select(Email).where(Email.message_id == message_id)
        )
        return result.scalar_one()
```

**Sharding (Advanced):**
```python
# Shard by api_key_id
def get_shard(api_key_id):
    return hash(api_key_id) % NUM_SHARDS

# Route to correct shard
shard = get_shard(api_key.id)
engine = shard_engines[shard]
```

---

### Monitoring & Observability

**1. Metrics to Track**
```python
from prometheus_client import Counter, Histogram

# Count emails sent
emails_sent = Counter(
    'emails_sent_total',
    'Total emails sent',
    ['status']  # Labels: sent, failed
)

# Track API latency
api_latency = Histogram(
    'api_request_duration_seconds',
    'API request latency'
)

# In code
emails_sent.labels(status='sent').inc()

with api_latency.time():
    process_request()
```

**Key Metrics:**
- **API latency** (p50, p95, p99)
- **Emails sent/failed** (rate, count)
- **Queue depth** (messages waiting)
- **Worker processing time**
- **Database query time**
- **Error rate**

---

**2. Logging & Tracing**
```python
# Structured logging
logger.info("Email sent", extra={
    "message_id": message_id,
    "to_email": to_email,
    "duration_ms": duration,
    "worker_id": worker_id
})

# Trace requests across services
import opentelemetry

with tracer.start_as_current_span("send_email"):
    with tracer.start_as_current_span("db_save"):
        save_to_db()
    with tracer.start_as_current_span("queue_publish"):
        publish_to_queue()
```

**Tools:**
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization
- **ELK Stack**: Logging (Elasticsearch, Logstash, Kibana)
- **Jaeger**: Distributed tracing

---

**3. Alerting**
```yaml
# Prometheus alert rules
groups:
  - name: email_service
    rules:
      - alert: HighErrorRate
        expr: rate(emails_sent_total{status="failed"}[5m]) > 0.1
        annotations:
          summary: "High email failure rate"

      - alert: QueueBacklog
        expr: rabbitmq_queue_messages{queue="email_queue"} > 10000
        annotations:
          summary: "Email queue is backed up"
```

---

### Security Hardening

**1. API Key Security**
```python
# Generate secure keys
import secrets

def generate_api_key():
    return f"sk_live_{secrets.token_urlsafe(32)}"

# Hash with salt
def hash_key(key: str):
    # Use bcrypt or argon2 in production
    return hashlib.pbkdf2_hmac(
        'sha256',
        key.encode(),
        salt.encode(),
        100000
    ).hex()
```

---

**2. Rate Limiting Enhancements**
```python
# Per-endpoint rate limits
RATE_LIMITS = {
    "/v1/emails": 60,        # 60/min
    "/v1/emails/{id}": 300   # 300/min (reads are cheaper)
}

# IP-based rate limiting (prevent abuse)
async def check_ip_rate_limit(request: Request):
    ip = request.client.host
    key = f"ip_ratelimit:{ip}"

    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60)

    if count > 100:  # Max 100 req/min per IP
        raise HTTPException(429, "IP rate limit exceeded")
```

---

**3. Input Validation**
```python
from pydantic import validator, EmailStr

class EmailSendRequest(BaseModel):
    to: EmailStr
    subject: str
    body_html: str | None

    @validator('subject')
    def validate_subject(cls, v):
        if len(v) > 500:
            raise ValueError("Subject too long")
        # Prevent injection attacks
        if any(c in v for c in ['<', '>', '\n', '\r']):
            raise ValueError("Invalid characters")
        return v

    @validator('body_html')
    def validate_html(cls, v):
        if v is None:
            return v
        # Sanitize HTML (prevent XSS)
        return bleach.clean(v, tags=ALLOWED_TAGS)
```

---

**4. HTTPS & Encryption**
```python
# In production, use HTTPS
# nginx config:
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://api:8000;
    }
}

# Encrypt sensitive data in database
from cryptography.fernet import Fernet

cipher = Fernet(encryption_key)

def encrypt_email_body(body: str) -> str:
    return cipher.encrypt(body.encode()).decode()

def decrypt_email_body(encrypted: str) -> str:
    return cipher.decrypt(encrypted.encode()).decode()
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Not Handling Connection Failures

**Problem:**
```python
# Bad: Crashes if RabbitMQ is down
connection = await aio_pika.connect(rabbitmq_url)
```

**Solution:**
```python
# Good: Retry with backoff
async def connect_with_retry(url, max_retries=5):
    for attempt in range(max_retries):
        try:
            return await aio_pika.connect_robust(url)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = 2 ** attempt
            logger.warning(f"Connection failed, retrying in {wait}s")
            await asyncio.sleep(wait)
```

---

### Pitfall 2: SQL Injection

**Problem:**
```python
# NEVER do this!
email = await db.execute(
    f"SELECT * FROM emails WHERE message_id = '{message_id}'"
)
# Attacker can send: message_id = "'; DROP TABLE emails; --"
```

**Solution:**
```python
# Always use parameterized queries
email = await db.execute(
    select(Email).where(Email.message_id == message_id)
)
# OR with raw SQL:
email = await db.execute(
    text("SELECT * FROM emails WHERE message_id = :id"),
    {"id": message_id}
)
```

---

### Pitfall 3: Not Validating Email Addresses

**Problem:**
```python
# Bad: Allows invalid emails
to_email = request.json["to"]  # Could be "not-an-email"
```

**Solution:**
```python
from pydantic import EmailStr

class EmailRequest(BaseModel):
    to: EmailStr  # Validates format automatically

# OR manual validation:
import re
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

def is_valid_email(email: str) -> bool:
    return re.match(EMAIL_REGEX, email) is not None
```

---

### Pitfall 4: Blocking Async Code

**Problem:**
```python
# Bad: Blocks event loop
async def send_email():
    time.sleep(2)  # Blocks entire server!
    smtp.send()    # Synchronous call
```

**Solution:**
```python
# Good: Use async alternatives
async def send_email():
    await asyncio.sleep(2)      # Non-blocking
    await smtp_async.send()     # Async SMTP

# If must use sync library:
import asyncio
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor()

async def send_email():
    # Run blocking code in thread pool
    await asyncio.get_event_loop().run_in_executor(
        executor,
        sync_smtp.send,
        email
    )
```

---

### Pitfall 5: Not Setting Message TTL

**Problem:**
```python
# Email stuck in queue for days
# User has moved on, email is now irrelevant
```

**Solution:**
```python
# Set message expiration
message = Message(
    body=json.dumps(data),
    expiration=3600  # Expire after 1 hour
)

# In worker, check timestamp
if email.created_at < datetime.now() - timedelta(hours=1):
    logger.info(f"Email {message_id} expired, skipping")
    return
```

---

## Conclusion

### What You've Learned

By building this email service, you've learned:

1. **System Design**: How to architect a scalable, reliable system
2. **Async Programming**: Non-blocking I/O for high performance
3. **Database Design**: Modeling data, relationships, indexes
4. **Message Queues**: Decoupling, reliability, scalability
5. **API Design**: RESTful endpoints, authentication, rate limiting
6. **Docker**: Containerization, orchestration
7. **Production Practices**: Monitoring, logging, error handling

---

### Next Steps

**Intermediate Enhancements:**
1. Add email templates (Jinja2)
2. Implement webhooks (notify app when email sent)
3. Add email tracking (open rates, click tracking)
4. Support attachments
5. Implement bounce handling

**Advanced Features:**
1. Multi-provider support (SendGrid, AWS SES fallback)
2. A/B testing (send variants, track performance)
3. Scheduled emails (send at specific time)
4. Email verification (check if address exists)
5. Compliance (GDPR, CAN-SPAM, unsubscribe)

**Scaling to Production:**
1. Kubernetes deployment
2. Multi-region setup (global latency)
3. Database sharding (millions of emails)
4. Advanced monitoring (APM, distributed tracing)
5. Cost optimization (AWS spot instances for workers)

---

### Resources for Further Learning

**Books:**
- "Designing Data-Intensive Applications" by Martin Kleppmann
- "High Performance Python" by Micha Gorelick
- "Database Internals" by Alex Petrov

**Online Courses:**
- FastAPI full course (TestDriven.io)
- RabbitMQ tutorials (RabbitMQ official)
- PostgreSQL Performance Tuning (Postgres Pro)

**Practice:**
- Build similar projects: SMS service, push notifications, task scheduler
- Contribute to open source: Celery, FastAPI, SQLAlchemy
- Read production codebases: Sentry, GitLab, Discourse

---

**Remember:** The best way to learn is by building. Start simple, make mistakes, iterate, and gradually add complexity. Every production system started as a simple prototype.

Good luck! 🚀
