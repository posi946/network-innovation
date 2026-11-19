"""Shared test fixtures (Day 5)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402
from app.models.database import UserProfile  # noqa: E402

try:
    from fastapi.testclient import TestClient
except ImportError:
    TestClient = None


@pytest.fixture
def client():
    if TestClient is None:
        pytest.skip("fastapi TestClient unavailable")
    return TestClient(app)


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer dev:test-user"}


@pytest.fixture
def free_user():
    return UserProfile(id="test-user", plan="free", analyses_this_month=0)


@pytest.fixture
def pro_user():
    return UserProfile(id="pro-user", plan="pro")


@pytest.fixture
def sample_contract():
    return ("This Non-Disclosure Agreement is entered into between the parties. "
            "The receiving party shall keep all confidential information secret. " * 30)


@pytest.fixture
def mock_claude(monkeypatch):
    from app.services import claude_client as module
    monkeypatch.setattr(module.claude_client, "_call", lambda system, user: (
        '{"document_type":"NDA","risk_level":"LOW","risk_score":12,'
        '"overall_verdict":"SIGN","verdict_reason":"Standard terms",'
        '"summary":"A standard NDA","red_flags":[]}'
    ))
    return module.claude_client
