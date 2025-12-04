import hashlib
from datetime import datetime
from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.database import get_db
from app.models import APIKey

settings = get_settings()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def hash_api_key(key: str) -> str:
    salted = f"{settings.api_key_salt}{key}"
    return hashlib.sha256(salted.encode()).hexdigest()


async def get_api_key(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """Validate API key and return the associated record."""
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Include X-API-Key header.",
        )

    key_prefix = api_key[:12] if len(api_key) >= 12 else api_key
    key_hash = hash_api_key(api_key)

    result = await db.execute(
        select(APIKey).where(
            APIKey.key_prefix == key_prefix,
            APIKey.key_hash == key_hash,
        )
    )
    api_key_record = result.scalar_one_or_none()

    if not api_key_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key.",
        )

    if not api_key_record.is_active:
        raise HTTPException(
            status_code=403,
            detail="API key is inactive.",
        )

    api_key_record.last_used_at = datetime.utcnow()
    await db.commit()

    return api_key_record


def create_api_key(name: str) -> tuple[str, str, str]:
    """Generate a new API key. Returns (full_key, key_prefix, key_hash)"""
    import secrets

    key_body = secrets.token_hex(24)
    full_key = f"sk_live_{key_body}"
    key_prefix = full_key[:12]
    key_hash = hash_api_key(full_key)

    return full_key, key_prefix, key_hash
