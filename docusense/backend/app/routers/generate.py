"""Document generation routes (Day 9)."""
from __future__ import annotations

import time
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import Response

from ..core.jurisdictions import get_jurisdiction
from ..middleware.auth import get_current_user
from ..middleware.rate_limit import check_usage_limit, enforce_rate_limit
from ..models.schemas import GenerateRequest
from ..services import analytics
from ..services.claude_client import claude_client
from ..services.doc_generator import doc_generator
from ..services.retriever import law_retriever

router = APIRouter(prefix="/api/generate", tags=["generate"])
_generated: dict[str, dict] = {}


@router.post("")
def generate_document(payload: GenerateRequest, user=Depends(get_current_user)):
    started = time.perf_counter()
    uid = str(user["id"])
    enforce_rate_limit(uid, "/api/generate")
    check_usage_limit(user, "generates")
    info = get_jurisdiction(payload.jurisdiction.upper()) or {}
    laws = ", ".join(info.get("laws", []))
    context = law_retriever.retrieve_for_document(payload.requirements, payload.jurisdiction.upper())
    content = claude_client.generate_document(
        payload.doc_type, payload.requirements, payload.jurisdiction.upper(),
        context, payload.party_a, payload.party_b, payload.language,
    )
    doc_id = str(uuid.uuid4())
    _generated[doc_id] = {
        "id": doc_id, "user_id": uid, "doc_type": payload.doc_type,
        "title": f"{payload.doc_type} — {payload.jurisdiction.upper()}",
        "jurisdiction": payload.jurisdiction.upper(), "content": content,
    }
    analytics.track_generate(uid, payload.jurisdiction, payload.doc_type,
                             round((time.perf_counter() - started) * 1000),
                             len(content.split()), getattr(user, "plan", "free"))
    return _generated[doc_id]


@router.get("/{document_id}/download")
def download_document(document_id: str, user=Depends(get_current_user)):
    doc = _generated.get(document_id)
    if not doc or doc["user_id"] != str(user["id"]):
        from fastapi import HTTPException
        raise HTTPException(404, "Document not found")
    doc["download_count"] = doc.get("download_count", 0) + 1
    data = doc_generator.generate_docx(
        doc["title"], doc["content"], doc["jurisdiction"], doc["doc_type"]
    )
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{doc["doc_type"]}.docx"'},
    )
