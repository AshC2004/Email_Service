from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api import emails, health
from app.db.database import init_db, close_db
from app.queue.publisher import init_rabbitmq, close_rabbitmq
from app.middleware.rate_limit import RateLimitMiddleware


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    await init_db()
    await init_rabbitmq()
    yield
    # shutdown
    await close_rabbitmq()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="Transactional email API service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS - TODO: restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)

app.include_router(health.router, tags=["Health"])
app.include_router(emails.router, prefix="/v1", tags=["Emails"])


@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
