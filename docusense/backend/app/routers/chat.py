"""Document, advisor and student chat routes (Day 9)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..core.jurisdictions import get_jurisdiction
from ..middleware.auth import get_current_user
from ..middleware.rate_limit import enforce_rate_limit
from ..models.schemas import AdvisorChatRequest, DocumentChatRequest, StudentChatRequest
from ..services.claude_client import claude_client
from ..services.retriever import law_retriever
from .analyze import _analyses

router = APIRouter(prefix="/api/chat", tags=["chat"])
_messages: dict[str, list[dict]] = {}


def _history(session_id: str) -> list[dict]:
    return _messages.setdefault(session_id, [])[-10:]


def _respond(user, session_id, jurisdiction, question, mode, history, language, analysis_id=None):
    enforce_rate_limit(str(user["id"]), "/api/chat")
    info = get_jurisdiction(jurisdiction.upper()) or {}
    laws = ", ".join(info.get("laws", []))
    context = law_retriever.retrieve_for_document(question, jurisdiction.upper())
    if mode == "advisor":
        text = claude_client.advisor_chat(question, jurisdiction.upper(), context, laws, history, language=language)
    elif mode == "student":
        text = claude_client.student_chat(question, jurisdiction.upper(), context, laws, history, "research", language=language)
    else:
        text = claude_client.advisor_chat(question, jurisdiction.upper(), context, laws, history, language=language)
    sid = session_id or str(uuid.uuid4())
    thread = _messages.setdefault(sid, [])
    thread.append({"role": "user", "content": question})
    thread.append({"role": "assistant", "content": text})
    return {"response": text, "session_id": sid, "citations": [], "analysis_id": analysis_id}


@router.post("/document")
def document_chat(payload: DocumentChatRequest, user=Depends(get_current_user)):
    if payload.analysis_id not in _analyses:
        raise HTTPException(404, "Analysis not found")
    return _respond(user, payload.session_id, _analyses[payload.analysis_id].get("jurisdiction", "NG"),
                    payload.message, "document", _history(payload.session_id or ""), payload.language,
                    payload.analysis_id)


@router.post("/advisor")
def advisor_chat(payload: AdvisorChatRequest, user=Depends(get_current_user)):
    return _respond(user, payload.session_id, payload.jurisdiction, payload.message, "advisor",
                    _history(payload.session_id or ""), payload.language)


@router.post("/student")
def student_chat(payload: StudentChatRequest, user=Depends(get_current_user)):
    return _respond(user, payload.session_id, payload.jurisdiction, payload.message, "student",
                    _history(payload.session_id or ""), payload.language)
