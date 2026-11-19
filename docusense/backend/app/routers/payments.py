"""Payment stubs — full safety implementation is Week 6 (Day 10)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/payments", tags=["payments"])
PLAN_PRICES = {"free": 0, "pro": 600000, "business": 2500000, "elite": 15000000}


@router.get("/plans")
def plans():
    return {
        plan: {"kobo": price, "display": "Free" if price == 0 else f"₦{price // 100:,}"}
        for plan, price in PLAN_PRICES.items()
    }


@router.post("/initiate")
def initiate():
    return JSONResponse(
        status_code=501,
        content={"message": "Payment system coming in Week 6. Use test mode for now."},
    )


@router.post("/webhook")
def webhook():
    return {"received": True}
