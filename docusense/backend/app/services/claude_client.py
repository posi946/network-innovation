"""Claude client with retries, timeouts and graceful fallback (Days 8 & 15)."""
from __future__ import annotations

import json
import time

from fastapi import HTTPException

from ..core import prompts
from ..core.config import settings
from ..core.sanitizer import sanitize_text

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1500


class ClaudeClient:
    def _call(self, system: str, user: str) -> str:
        if not settings.anthropic_api_key:
            return self._offline_response(user)
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=30.0)
            for attempt in range(2):
                try:
                    msg = client.messages.create(
                        model=MODEL, max_tokens=MAX_TOKENS,
                        system=system,
                        messages=[{"role": "user", "content": user}],
                    )
                    return msg.content[0].text
                except Exception as exc:
                    name = type(exc).__name__
                    if "Connection" in name and attempt == 0:
                        time.sleep(0.4)
                        continue
                    if "RateLimit" in name:
                        raise HTTPException(504, "Analysis is taking longer than expected. Try again.")
                    if "BadRequest" in name:
                        raise HTTPException(400, "Document is too long. Try a shorter document.")
                    raise
        except HTTPException:
            raise
        except Exception:
            return json.dumps({"error": "analysis_unavailable",
                               "suggestion": "Try a shorter document or try again in a moment"})

    def analyze_document(self, text, jurisdiction, law_context, laws_list, language="en"):
        system = prompts.analysis_system_prompt(jurisdiction, laws_list, language)
        return self._call(system, prompts.analysis_user_template(text))

    def analyze_with_image(self, b64, media_type, jurisdiction, law_context, laws_list, language="en"):
        system = prompts.analysis_system_prompt(jurisdiction, laws_list, language)
        user = f"{law_context}\nAnalyse this image of a document. Return the same JSON structure."
        return self._call(system, user)

    def generate_document(self, doc_type, requirements, jurisdiction, law_context, party_a, party_b, language="en"):
        return self._call(
            prompts.generation_system_prompt(jurisdiction, language),
            f"Draft a {doc_type}. Party A: {party_a}. Party B: {party_b}. "
            f"Requirements: {sanitize_text(requirements)}. Law: {law_context}",
        )

    def advisor_chat(self, question, jurisdiction, law_context, laws_list, history, case_context="", language="en"):
        return self._call(
            prompts.advisor_system_prompt(jurisdiction, language),
            f"History: {history}\nLaw: {law_context}\nCases: {case_context}\nQuestion: {sanitize_text(question)}",
        )

    def student_chat(self, question, jurisdiction, law_context, laws_list, history, mode, case_context="", language="en"):
        return self._call(
            prompts.student_system_prompt(jurisdiction, language),
            f"Mode: {mode}\nHistory: {history}\nLaw: {law_context}\nQuestion: {sanitize_text(question)}",
        )

    def voice_chat(self, transcript, jurisdiction, law_context, laws_list, history, intent, language="en"):
        return self._call(
            prompts.voice_system_prompt(jurisdiction, language),
            f"Intent: {intent}\nHistory: {history}\nLaw: {law_context}\nTranscript: {transcript}",
        )

    @staticmethod
    def _offline_response(user: str) -> str:
        return json.dumps({
            "document_type": "Contract", "risk_level": "MEDIUM", "risk_score": 42,
            "overall_verdict": "NEGOTIATE",
            "verdict_reason": "Offline demo analysis — connect ANTHROPIC_API_KEY for full analysis.",
            "summary": user[:200], "red_flags": [], "missing_clauses": [],
            "negotiation_points": [], "questions_to_ask": [],
        })


claude_client = ClaudeClient()
