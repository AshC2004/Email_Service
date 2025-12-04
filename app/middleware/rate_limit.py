import redis.asyncio as redis
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings

settings = get_settings()

_redis_pool = None


async def get_redis() -> redis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def close_redis():
    global _redis_pool
    if _redis_pool:
        await _redis_pool.close()
        _redis_pool = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith("/v1"):
            return await call_next(request)

        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return await call_next(request)

        try:
            redis_client = await get_redis()

            key = f"ratelimit:{api_key[:12]}"

            current = await redis_client.incr(key)

            if current == 1:
                await redis_client.expire(key, 60)

            ttl = await redis_client.ttl(key)

            # TODO: fetch actual limit from API key record
            limit = 60

            request.state.rate_limit_limit = limit
            request.state.rate_limit_remaining = max(0, limit - current)
            request.state.rate_limit_reset = ttl

            if current > limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Try again in {ttl} seconds.",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(ttl),
                        "Retry-After": str(ttl),
                    }
                )

        except redis.RedisError:
            # fail open if redis is down
            pass

        response = await call_next(request)

        if hasattr(request.state, "rate_limit_limit"):
            response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
            response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
            response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)

        return response
