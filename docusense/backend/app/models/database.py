"""SQLAlchemy models and session helpers (Day 2)."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Iterator

from ..core.config import settings

try:
    from sqlalchemy import (
        Boolean, Column, DateTime, ForeignKey, Integer, JSON, SmallInteger,
        String, Text, Uuid, create_engine, func, text,
    )
    from sqlalchemy.orm import declarative_base, relationship, sessionmaker
    _SQLALCHEMY = True
except ImportError:
    _SQLALCHEMY = False

if _SQLALCHEMY:
    Base = declarative_base()

    class UserProfile(Base):
        __tablename__ = "user_profiles"
        id = Column(Uuid, primary_key=True)
        full_name = Column(String, default="")
        email = Column(String)
        companion_name = Column(String, default="Lex")
        companion_color = Column(String, default="violet")
        companion_voice = Column(String, default="nova")
        preferred_language = Column(String, default="en")
        plan = Column(String, default="free")
        default_jurisdiction = Column(String, default="NG")
        analyses_this_month = Column(Integer, default=0)
        generates_this_month = Column(Integer, default=0)
        organization_id = Column(Uuid, ForeignKey("organizations.id"), nullable=True)

        analyses = relationship("Analysis", back_populates="user")
        documents = relationship("Document", back_populates="user")
        organization = relationship("Organization", back_populates="owner")

        @property
        def is_free(self) -> bool:
            return self.plan == "free"

        @property
        def can_analyze(self) -> bool:
            return self.plan != "free" or self.analyses_this_month < 2

        @property
        def can_generate(self) -> bool:
            return self.plan != "free" or self.generates_this_month < 1

        @property
        def is_org_member(self) -> bool:
            return self.organization_id is not None

    class Organization(Base):
        __tablename__ = "organizations"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        name = Column(String, nullable=False)
        owner_id = Column(Uuid, ForeignKey("user_profiles.id"))
        plan = Column(String, default="business")
        seat_count = Column(Integer, default=5)
        invite_token = Column(String, unique=True, nullable=True)
        owner = relationship("UserProfile", back_populates="organization")
        members = relationship("OrganizationMember", back_populates="organization")

    class OrganizationMember(Base):
        __tablename__ = "organization_members"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        organization_id = Column(Uuid, ForeignKey("organizations.id"))
        user_id = Column(Uuid, ForeignKey("user_profiles.id"))
        role = Column(String, default="member")
        organization = relationship("Organization", back_populates="members")

    class Document(Base):
        __tablename__ = "documents"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        user_id = Column(Uuid, ForeignKey("user_profiles.id"))
        file_name = Column(String)
        original_name = Column(String)
        file_type = Column(String)
        file_size_kb = Column(Integer)
        storage_path = Column(String)
        jurisdiction = Column(String, default="NG")
        raw_text = Column(Text)
        was_camera = Column(Boolean, default=False)
        ocr_used = Column(Boolean, default=False)
        deleted_at = Column(DateTime, nullable=True)
        user = relationship("UserProfile", back_populates="documents")

    class Analysis(Base):
        __tablename__ = "analyses"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        document_id = Column(Uuid, ForeignKey("documents.id"), nullable=True)
        user_id = Column(Uuid, ForeignKey("user_profiles.id"))
        jurisdiction = Column(String)
        document_type = Column(String)
        risk_level = Column(String)
        risk_score = Column(SmallInteger)
        overall_verdict = Column(String)
        verdict_reason = Column(Text)
        summary = Column(Text)
        red_flags = Column(JSON, default=list)
        missing_clauses = Column(JSON, default=list)
        negotiation_points = Column(JSON, default=list)
        questions_to_ask = Column(JSON, default=list)
        duration_ms = Column(Integer, default=0)
        user = relationship("UserProfile", back_populates="analyses")

    class GeneratedDocument(Base):
        __tablename__ = "generated_documents"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        user_id = Column(Uuid, ForeignKey("user_profiles.id"))
        doc_type = Column(String)
        title = Column(String)
        jurisdiction = Column(String)
        content = Column(Text)
        download_count = Column(Integer, default=0)

    class ChatMessage(Base):
        __tablename__ = "chat_messages"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        user_id = Column(Uuid, ForeignKey("user_profiles.id"))
        session_id = Column(Uuid, default=uuid.uuid4)
        analysis_id = Column(Uuid, ForeignKey("analyses.id"), nullable=True)
        chat_type = Column(String)
        jurisdiction = Column(String)
        role = Column(String)
        content = Column(Text)
        message_index = Column(Integer, default=0)
        citations = Column(JSON, default=list)

    class LawChunk(Base):
        __tablename__ = "law_chunks"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        country = Column(String)
        law_type = Column(String)
        law_title = Column(String)
        section = Column(String)
        content = Column(Text)
        language = Column(String, default="en")
        source_url = Column(String)
        embedding = Column(String)  # vector(1024) in production

    class VoiceSession(Base):
        __tablename__ = "voice_sessions"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        user_id = Column(Uuid, ForeignKey("user_profiles.id"))
        session_id = Column(Uuid, default=uuid.uuid4)
        jurisdiction = Column(String)
        companion_name = Column(String, default="Lex")
        wake_word_count = Column(Integer, default=0)
        total_turns = Column(Integer, default=0)
        duration_seconds = Column(Integer, default=0)
        intents_used = Column(JSON, default=list)

    class AuditLog(Base):
        __tablename__ = "audit_logs"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        user_id = Column(Uuid, nullable=True)
        action = Column(String)
        ip_address = Column(String)
        user_agent = Column(String)
        endpoint = Column(String)
        method = Column(String)
        status_code = Column(Integer)
        duration_ms = Column(Integer)

    class FeatureFlag(Base):
        __tablename__ = "feature_flags"
        id = Column(Uuid, primary_key=True, default=uuid.uuid4)
        flag_key = Column(String, unique=True)
        description = Column(String)
        enabled = Column(Boolean, default=False)
        rollout_percent = Column(Integer, default=0)
        allowed_plans = Column(JSON, default=list)

else:
    class Base:  # type: ignore
        pass

    @dataclass
    class UserProfile:
        id: Any = field(default_factory=lambda: str(uuid.uuid4()))
        plan: str = "free"
        analyses_this_month: int = 0
        generates_this_month: int = 0
        companion_name: str = "Lex"
        preferred_language: str = "en"
        default_jurisdiction: str = "NG"

        @property
        def is_free(self): return self.plan == "free"
        @property
        def can_analyze(self): return self.plan != "free" or self.analyses_this_month < 2
        @property
        def can_generate(self): return self.plan != "free" or self.generates_this_month < 1
        @property
        def is_org_member(self): return False

    @dataclass
    class Analysis:
        id: Any = field(default_factory=lambda: str(uuid.uuid4()))
        document_type: str = ""
        risk_level: str = "LOW"
        risk_score: int = 0
        overall_verdict: str = "NEGOTIATE"
        verdict_reason: str = ""
        summary: str = ""

    Document = ChatMessage = LawChunk = VoiceSession = FeatureFlag = object
    GeneratedDocument = Analysis
    Organization = OrganizationMember = object


_engine = None
_SessionLocal = None


def get_engine():
    global _engine, _SessionLocal
    if _engine is None and _SQLALCHEMY:
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_db() -> Iterator[Any]:
    if _SQLALCHEMY:
        get_engine()
        db = _SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        yield None


_audit_memory: list[dict] = []


def log_audit(**kwargs) -> None:
    """Append-only audit log (in-memory fallback when no DB is configured)."""
    record = dict(kwargs)
    record.setdefault("created_at", time.time())
    _audit_memory.append(record)
    if _SQLALCHEMY and settings.database_url.startswith("postgresql"):
        try:
            with get_engine().begin() as conn:
                conn.execute(
                    text("INSERT INTO audit_logs (id, user_id, action, ip_address, user_agent, "
                         "endpoint, method, status_code, duration_ms, created_at) "
                         "VALUES (gen_random_uuid(), :user_id, :action, :ip, :ua, :endpoint, "
                         ":method, :status, :duration, NOW())"),
                    {
                        "user_id": record.get("user_id"), "action": record.get("action"),
                        "ip": record.get("ip"), "ua": record.get("user_agent"),
                        "endpoint": record.get("endpoint"), "method": record.get("method"),
                        "status": record.get("status_code"), "duration": record.get("duration_ms"),
                    },
                )
        except Exception:
            pass


def audit_records() -> list[dict]:
    return list(_audit_memory)
