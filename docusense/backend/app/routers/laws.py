"""Law search routes (Day 9)."""
from __future__ import annotations

from fastapi import APIRouter

from ..core.jurisdictions import all_jurisdictions
from ..models.schemas import LawSearchRequest
from ..services.retriever import law_retriever

router = APIRouter(prefix="/api/laws", tags=["laws"])


@router.post("/search")
def search_laws(payload: LawSearchRequest):
    return law_retriever.retrieve(payload.query, payload.country.upper(), top_k=payload.top_k)


@router.get("/jurisdictions")
def jurisdictions():
    return all_jurisdictions()
