"""Document upload and management (Day 8)."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from ..core.jurisdictions import VALID_CODES
from ..core.sanitizer import sanitize_filename, sanitize_jurisdiction
from ..middleware.auth import get_current_user
from ..middleware.rate_limit import enforce_rate_limit
from ..services.document_parser import document_parser
from ..services.file_validator import file_validator

router = APIRouter(prefix="/api/documents", tags=["documents"])
_documents: dict[str, dict] = {}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    jurisdiction: str = Form("NG"),
    user=Depends(get_current_user),
):
    enforce_rate_limit(str(user["id"]), "/api/documents/upload")
    jurisdiction = sanitize_jurisdiction(jurisdiction, VALID_CODES)
    content = await file.read()
    mime = file_validator.validate_file(content, file.filename or "document", file.content_type or "")
    text = document_parser.parse(content, mime, file.filename or "")
    doc_id = str(uuid.uuid4())
    name = sanitize_filename(file.filename or "document")
    _documents[doc_id] = {
        "id": doc_id, "user_id": str(user["id"]), "file_name": name,
        "jurisdiction": jurisdiction, "raw_text": text,
    }
    return {
        "document_id": doc_id, "file_name": name,
        "text_preview": text[:200], "jurisdiction": jurisdiction, "status": "ready",
    }


@router.get("")
def list_documents(user=Depends(get_current_user)):
    uid = str(user["id"])
    return [d for d in _documents.values() if d["user_id"] == uid][-20:]


@router.delete("/{document_id}")
def delete_document(document_id: str, user=Depends(get_current_user)):
    doc = _documents.get(document_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    if doc["user_id"] != str(user["id"]):
        raise HTTPException(403, "Forbidden")
    doc["deleted_at"] = "now"
    return {"status": "deleted"}


def get_document(document_id: str, user_id: str) -> dict:
    doc = _documents.get(document_id)
    if not doc or doc["user_id"] != user_id:
        raise HTTPException(404, "Document not found")
    return doc
