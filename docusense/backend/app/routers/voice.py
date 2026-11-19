"""Voice routes with sanitization and session continuity (Days 9 & 15)."""
from __future__ import annotations

import re
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..core.jurisdictions import get_jurisdiction
from ..core.sanitizer import SecurityError, sanitize_voice_transcript
from ..middleware.auth import get_current_user
from ..middleware.rate_limit import enforce_rate_limit
from ..models.schemas import VoiceChatRequest
from ..services.claude_client import claude_client
from ..services.retriever import law_retriever
from .chat import _messages

router = APIRouter(prefix="/api/voice", tags=["voice"])
_sessions: dict[str, dict] = {}


def _navigate(intent: str, transcript: str) -> str | None:
    if intent == "ANALYZE_DOCUMENT" or re.search(r"analy[sz]e|check this contract", transcript, re.I):
        return "analyze"
    if intent == "GENERATE_DOCUMENT" or re.search(r"draft|generate|write a contract", transcript, re.I):
        return "generate"
    return None


@router.post("")
def voice_chat(payload: VoiceChatRequest, user=Depends(get_current_user)):
    uid = str(user["id"])
    enforce_rate_limit(uid, "/api/voice")
    try:
        transcript = sanitize_voice_transcript(payload.transcript)
    except SecurityError as exc:
        raise HTTPException(400, str(exc))

    session_id = payload.session_id or str(uuid.uuid4())
    session = _sessions.setdefault(session_id, {
        "user_id": uid, "session_id": session_id, "total_turns": 0,
        "intents_used": [], "started": time.time(),
    })
    info = get_jurisdiction(payload.jurisdiction.upper()) or {}
    laws = ", ".join(info.get("laws", []))
    context = law_retriever.retrieve_for_document(transcript, payload.jurisdiction.upper())
    history = _messages.setdefault(session_id, [])[-10:]
    response_text = claude_client.voice_chat(
        transcript, payload.jurisdiction.upper(), context, laws, history,
        payload.intent.value, payload.language,
    )
    _messages[session_id].append({"role": "user", "content": transcript})
    _messages[session_id].append({"role": "assistant", "content": response_text})
    session["total_turns"] += 1
    session["intents_used"].append(payload.intent.value)
    session["duration_seconds"] = int(time.time() - session["started"])

    return {
        "response_text": response_text,
        "session_id": session_id,
        "intent_processed": payload.intent.value,
        "should_navigate_to": _navigate(payload.intent.value, transcript),
        "voice_session_stats": {
            "total_turns": session["total_turns"],
            "intents_used": session["intents_used"],
            "duration_seconds": session["duration_seconds"],
        },
    }
