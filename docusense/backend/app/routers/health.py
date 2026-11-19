"""Health check endpoint (Day 5)."""
from __future__ import annotations

import time

from fastapi import APIRouter

from ..core.config import settings

router = APIRouter(prefix="", tags=["health"])
_STARTED = time.time()
VERSION = "0.1.0"


@router.get("/health")
def health():
    db_connected = False
    try:
        from ..models.database import get_engine
        engine = get_engine()
        if engine is not None:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            db_connected = True
    except Exception:
        db_connected = False
    return {
        "status": "ok" if db_connected or settings.environment != "production" else "degraded",
        "version": VERSION,
        "environment": settings.environment,
        "db_connected": db_connected,
        "uptime_seconds": round(time.time() - _STARTED, 2),
    }
