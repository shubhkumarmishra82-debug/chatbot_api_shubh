"""
API-key authentication + per-key rate limiting for /v1/chat/completions.
Rate limiting is DB-backed (a sliding 60s window stored on the ApiKey
row) rather than in-memory, since serverless functions don't share
memory between invocations -- an in-memory counter would silently reset
on every cold start and not actually limit anything.
"""
import os
import time

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session

from . import database

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))


def get_api_key_row(
    authorization: str = Header(None),
    db: Session = Depends(database.get_db),
) -> database.ApiKey:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing API key. Send: Authorization: Bearer <your_key>. "
                   "Get one at /api.",
        )
    key_value = authorization.split(" ", 1)[1].strip()
    row = db.query(database.ApiKey).filter(database.ApiKey.key == key_value).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid API key.")
    return row


def enforce_rate_limit(row: database.ApiKey, db: Session):
    now = time.time()
    window_start = row.rate_limit_window_start or 0.0

    if now - window_start > 60:
        row.rate_limit_window_start = now
        row.rate_limit_count = 0

    if (row.rate_limit_count or 0) >= RATE_LIMIT_PER_MINUTE:
        retry_after = max(1, int(60 - (now - window_start)))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({RATE_LIMIT_PER_MINUTE}/min). Retry in ~{retry_after}s.",
        )

    row.rate_limit_count = (row.rate_limit_count or 0) + 1
    db.commit()


def require_api_key(
    row: database.ApiKey = Depends(get_api_key_row),
    db: Session = Depends(database.get_db),
) -> database.ApiKey:
    enforce_rate_limit(row, db)
    return row
