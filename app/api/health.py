from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    """Check health of all service dependencies."""
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "unhealthy"

    rabbitmq_status = "healthy"
    try:
        from app.queue.publisher import get_connection
        conn = await get_connection()
        if conn is None or conn.is_closed:
            rabbitmq_status = "unhealthy"
    except Exception:
        rabbitmq_status = "unhealthy"

    redis_status = "healthy"
    try:
        from app.middleware.rate_limit import get_redis
        redis_client = await get_redis()
        await redis_client.ping()
    except Exception:
        redis_status = "unhealthy"

    overall = "healthy"
    if any(s == "unhealthy" for s in [db_status, rabbitmq_status, redis_status]):
        overall = "degraded"

    return HealthResponse(
        status=overall,
        database=db_status,
        rabbitmq=rabbitmq_status,
        redis=redis_status,
        timestamp=datetime.utcnow(),
    )


@router.get("/health/live")
async def liveness():
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
