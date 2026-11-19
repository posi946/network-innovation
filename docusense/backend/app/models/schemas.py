"""Pydantic request/response schemas (Day 2)."""
from __future__ import annotations

import re
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, field_validator

from ..core.jurisdictions import VALID_CODES
from ..core.sanitizer import sanitize_text


class Plan(str, Enum):
    free = "free"
    pro = "pro"
    business = "business"
    elite = "elite"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Verdict(str, Enum):
    SIGN = "SIGN"
    NEGOTIATE = "NEGOTIATE"
    DO_NOT_SIGN = "DO NOT SIGN"


class ChatType(str, Enum):
    document = "document"
    advisor = "advisor"
    student = "student"
    irac = "irac"
    voice = "voice"


class StudentMode(str, Enum):
    research = "research"
    irac = "irac"
    quiz = "quiz"
    citation = "citation"


class LawType(str, Enum):
    constitution = "constitution"
    statute = "statute"
    regulation = "regulation"
    case_law = "case_law"
    treaty = "treaty"


class VoiceIntent(str, Enum):
    ANALYZE_DOCUMENT = "ANALYZE_DOCUMENT"
    GENERATE_DOCUMENT = "GENERATE_DOCUMENT"
    ASK_QUESTION = "ASK_QUESTION"
    IRAC_MEMO = "IRAC_MEMO"
    GENERAL_CHAT = "GENERAL_CHAT"


class OrgRole(str, Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class OrbColor(str, Enum):
    violet = "violet"; cyan = "cyan"; gold = "gold"; ember = "ember"
    arctic = "arctic"; jade = "jade"; rose = "rose"; solar = "solar"


class CompanionVoice(str, Enum):
    nova = "nova"; sterling = "sterling"; quinn = "quinn"; sydney = "sydney"
    anika = "anika"; amara = "amara"; zara = "zara"; lena = "lena"; sage = "sage"


class Language(str, Enum):
    en = "en"; fr = "fr"; ar = "ar"; pt = "pt"; sw = "sw"; yo = "yo"
    ha = "ha"; ig = "ig"; es = "es"; de = "de"; zh = "zh"; hi = "hi"


VOICE_TO_BROWSER_NAME: dict[CompanionVoice, list[str]] = {
    CompanionVoice.nova: ["Google UK English Female", "Samantha", "Karen"],
    CompanionVoice.sterling: ["Google UK English Male", "Daniel", "Arthur"],
    CompanionVoice.quinn: ["Google US English", "Alex", "Zira"],
    CompanionVoice.sydney: ["Google Australian English", "Karen", "Lee"],
    CompanionVoice.anika: ["Google हिन्दी", "Rishi", "Veena"],
    CompanionVoice.amara: ["Google français", "Thomas", "Amélie"],
    CompanionVoice.zara: ["Google العربية", "Maged", "Laila"],
    CompanionVoice.lena: ["Google português do Brasil", "Luciana", "Joana"],
    CompanionVoice.sage: ["Samantha", "Moira", "Fiona"],
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LanguageField(StrictModel):
    language: Optional[Language] = "en"

    @field_validator("language")
    @classmethod
    def _language(cls, v): return v or Language.en


class AnalyzeRequest(LanguageField):
    document_id: str
    jurisdiction: str

    @field_validator("jurisdiction")
    @classmethod
    def _jurisdiction(cls, v): return v.upper() if v.upper() in VALID_CODES else v


class AnalyzeImageRequest(LanguageField):
    image_base64: str
    media_type: str
    jurisdiction: str


class GenerateRequest(LanguageField):
    doc_type: str
    jurisdiction: str
    party_a: str = ""
    party_b: str = ""
    requirements: str


class DocumentChatRequest(LanguageField):
    analysis_id: str
    message: str
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _clean(cls, v): return sanitize_text(v)


class AdvisorChatRequest(LanguageField):
    message: str
    jurisdiction: str
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _clean(cls, v): return sanitize_text(v)


class StudentChatRequest(LanguageField):
    message: str
    jurisdiction: str
    mode: StudentMode = StudentMode.research
    session_id: Optional[str] = None

    @field_validator("message")
    @classmethod
    def _clean(cls, v): return sanitize_text(v)


class VoiceChatRequest(LanguageField):
    transcript: str
    intent: VoiceIntent = VoiceIntent.GENERAL_CHAT
    jurisdiction: str
    session_id: Optional[str] = None
    context_history: list[dict[str, str]] = []


class LawSearchRequest(StrictModel):
    query: str
    country: str
    law_type: Optional[LawType] = None
    top_k: int = 6


class CompanionNameUpdateRequest(StrictModel):
    companion_name: str

    @field_validator("companion_name")
    @classmethod
    def _name(cls, v):
        if not re.fullmatch(r"[A-Za-z]{1,20}", v):
            raise ValueError("Companion name must be 1-20 letters")
        return v


class CompanionSettingsUpdateRequest(StrictModel):
    companion_name: str
    companion_color: OrbColor
    companion_voice: CompanionVoice
    preferred_language: Language


class ToSAcceptRequest(StrictModel):
    version: str


class AnalysisResponse(StrictModel):
    id: str
    document_type: str
    risk_level: RiskLevel
    risk_score: int
    overall_verdict: Verdict
    verdict_reason: str
    summary: str
    red_flags: list[str] = []
    missing_clauses: list[str] = []
    negotiation_points: list[str] = []
    questions_to_ask: list[str] = []


class ChatResponse(StrictModel):
    response: str
    session_id: str
    citations: list[str] = []


class VoiceResponse(StrictModel):
    response_text: str
    session_id: str
    intent_processed: str
    should_navigate_to: Optional[str] = None
    voice_session_stats: dict[str, Any] = {}
