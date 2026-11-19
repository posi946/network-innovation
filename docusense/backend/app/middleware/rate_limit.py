"""Rate limiting and monthly plan gating (Day 4)."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException

PLAN_LIMITS = {"free": {"analyses": 2, "generates": 1}}
UNLIMITED = {"pro", "business", "elite"}

_LIMITS = {
    "/api/analyze": (10, 60),
    "/api/analyze/image": (10, 60),
    "/api/generate": (5, 60),
    "/api/chat": (30, 60),
    "/api/voice": (20, 60),
    "/api/documents/upload": (20, 3600),
}
_hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
_monthly: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))


def enforce_rate_limit(key: str, path: str) -> None:
    if path not in _LIMITS:
        return
    limit, window = _LIMITS[path]
    bucket = _hits[(key, path)]
    now = time.time()
    while bucket and bucket[0] < now - window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(429, "Rate limit exceeded. Please slow down.")
    bucket.append(now)


def check_usage_limit(user, action: str, db=None) -> None:
    plan = getattr(user, "plan", "free") or "free"
    if plan in UNLIMITED:
        return
    allowed = PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get(action, 0)
    uid = str(getattr(user, "id", "anonymous"))
    used = _monthly[uid][action]
    if used >= allowed:
        raise HTTPException(402, {
            "error": f"Monthly {action} limit reached for the {plan} plan",
            "upgrade_url": "/pricing",
            "current_plan": plan,
        })
    _monthly[uid][action] = used + 1


def reset_monthly_usage(user_id: str) -> None:
    _monthly.pop(str(user_id), None)
