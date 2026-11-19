"""Server-side analytics (Day 10)."""
from __future__ import annotations

from ..core.config import settings

_events: list[dict] = []


def _track(name: str, properties: dict) -> None:
    record = {"event": name, **properties}
    _events.append(record)
    if settings.posthog_api_key:
        try:
            from posthog import Posthog
            client = Posthog(settings.posthog_api_key, host="https://us.i.posthog.com")
            client.capture(properties.get("user_id", "anonymous"), name, properties)
        except Exception:
            pass


def track_analysis(user_id, country, doc_type, risk_level, risk_score, red_flags_count, duration_ms, was_camera, plan):
    _track("analysis_completed", dict(user_id=user_id, country=country, doc_type=doc_type,
           risk_level=risk_level, risk_score=risk_score, red_flags=red_flags_count,
           duration_ms=duration_ms, was_camera=was_camera, plan=plan))


def track_generate(user_id, country, doc_type, duration_ms, word_count, plan):
    _track("document_generated", dict(user_id=user_id, country=country, doc_type=doc_type,
           duration_ms=duration_ms, word_count=word_count, plan=plan))


def track_voice_session(user_id, country, turns, duration_sec, intents_used):
    _track("voice_session", dict(user_id=user_id, country=country, turns=turns,
           duration_sec=duration_sec, intents=intents_used))


def track_limit_hit(user_id, feature, plan):
    _track("limit_hit", dict(user_id=user_id, feature=feature, plan=plan))


def track_api_performance(endpoint, duration_ms, status_code, plan, country):
    _track("api_performance", dict(endpoint=endpoint, duration_ms=duration_ms,
           status_code=status_code, plan=plan, country=country))


def events() -> list[dict]:
    return list(_events)
