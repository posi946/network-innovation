"""Analysis routes (Day 9)."""
from __future__ import annotations

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..core.jurisdictions import get_jurisdiction
from ..middleware.auth import get_current_user
from ..middleware.rate_limit import check_usage_limit, enforce_rate_limit
from ..models.schemas import AnalyzeImageRequest, AnalyzeRequest
from ..services import analytics
from ..services.claude_client import claude_client
from ..services.retriever import law_retriever
from .documents import get_document

router = APIRouter(prefix="/api", tags=["analyze"])
_analyses: dict[str, dict] = {}


def _run_analysis(user, jurisdiction: str, text: str, image: bool, language: str):
    started = time.perf_counter()
    enforce_rate_limit(str(user["id"]), "/api/analyze/image" if image else "/api/analyze")
    check_usage_limit(user, "analyses")
    info = get_jurisdiction(jurisdiction) or {}
    laws = ", ".join(info.get("laws", []))
    law_context = law_retriever.retrieve_for_document(text, jurisdiction)
    raw = (claude_client.analyze_with_image(text, "image/jpeg", jurisdiction, law_context, laws, language)
           if image else claude_client.analyze_document(text, jurisdiction, law_context, laws, language))
    try:
        data = json.loads(raw)
    except Exception:
        data = {"summary": raw, "risk_level": "MEDIUM", "risk_score": 50,
                "overall_verdict": "NEGOTIATE", "document_type": "Contract"}
    data.setdefault("red_flags", [])
    data.setdefault("missing_clauses", [])
    data.setdefault("negotiation_points", [])
    data.setdefault("questions_to_ask", [])
    data["id"] = str(uuid.uuid4())
    _analyses[data["id"]] = data
    duration = round((time.perf_counter() - started) * 1000)
    analytics.track_analysis(user["id"], jurisdiction, data.get("document_type"),
                             data.get("risk_level"), data.get("risk_score"),
                             len(data.get("red_flags", [])), duration, image,
                             getattr(user, "plan", "free"))
    return data


@router.post("/analyze")
def analyze_document(payload: AnalyzeRequest, user=Depends(get_current_user)):
    doc = get_document(payload.document_id, str(user["id"]))
    return _run_analysis(user, payload.jurisdiction.upper(), doc["raw_text"], False, payload.language)


@router.post("/analyze/image")
def analyze_image(payload: AnalyzeImageRequest, user=Depends(get_current_user)):
    return _run_analysis(user, payload.jurisdiction.upper(), payload.image_base64, True, payload.language)


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str, user=Depends(get_current_user)):
    result = _analyses.get(analysis_id)
    if not result:
        raise HTTPException(404, "Analysis not found")
    return result
