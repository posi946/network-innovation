"""FastAPI application entrypoint (Days 1, 3, 5)."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings
from .middleware.security import SecurityAndLoggingMiddleware
from .routers import analyze, chat, documents, generate, health, laws, payments, voice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("docusense")

app = FastAPI(title="DocuSense Africa v2", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityAndLoggingMiddleware)

for module in (health, documents, analyze, generate, chat, voice, laws, payments):
    app.include_router(module.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    if settings.is_production:
        return JSONResponse(status_code=500, content={"error": "Internal server error"})
    return JSONResponse(status_code=500, content={"error": str(exc)})


@app.on_event("startup")
async def on_startup():
    logger.info("DocuSense API started in %s mode", settings.environment)
    if settings.configuration_warnings:
        logger.warning("Missing optional config: %s", ", ".join(settings.configuration_warnings))
