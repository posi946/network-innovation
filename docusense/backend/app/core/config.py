"""Application settings.

Mirrors pydantic-settings BaseSettings behaviour but falls back to a stdlib
implementation so the project boots in lightweight environments.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

_REQUIRED = (
    "ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY",
    "SUPABASE_ANON_KEY", "SUPABASE_JWT_SECRET", "COHERE_API_KEY",
    "PAYSTACK_SECRET_KEY", "PAYSTACK_PUBLIC_KEY", "PAYSTACK_WEBHOOK_SECRET",
    "SECRET_KEY", "DATABASE_URL",
)


def _load_dotenv() -> None:
    path = Path(".env")
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Settings:
    def __init__(self, strict: bool = False) -> None:
        _load_dotenv()
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql+psycopg2://postgres:postgres@postgres:5432/docusense"
        )
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.cohere_api_key = os.getenv("COHERE_API_KEY", "")
        self.laws_africa_token = os.getenv("LAWS_AFRICA_TOKEN", "")
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.supabase_anon_key = os.getenv("SUPABASE_ANON_KEY", "")
        self.supabase_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "")
        self.paystack_secret_key = os.getenv("PAYSTACK_SECRET_KEY", "")
        self.paystack_public_key = os.getenv("PAYSTACK_PUBLIC_KEY", "")
        self.paystack_webhook_secret = os.getenv("PAYSTACK_WEBHOOK_SECRET", "")
        self.sentry_dsn = os.getenv("SENTRY_DSN", "")
        self.posthog_api_key = os.getenv("POSTHOG_API_KEY", "")
        self.brevo_api_key = os.getenv("BREVO_API_KEY", "")
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
        self.allowed_origins: List[str] = [
            o.strip() for o in os.getenv(
                "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8765"
            ).split(",") if o.strip()
        ]
        missing = [k for k in _REQUIRED if not os.getenv(k)]
        self.configuration_warnings = missing
        if strict and self.is_production and missing:
            raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def is_debug(self) -> bool:
        return not self.is_production

    @property
    def allowed_origins_list(self) -> List[str]:
        return self.allowed_origins


settings = Settings()
