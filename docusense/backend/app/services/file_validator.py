"""File validation with real MIME detection (Day 4)."""
from __future__ import annotations

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 50

_ALLOWED = {
    "application/pdf", "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/jpeg", "image/png",
}


class FileValidationError(ValueError):
    pass


class FileValidator:
    def validate_file(self, file_bytes: bytes, file_name: str, declared_type: str = "") -> str:
        if len(file_bytes) > MAX_BYTES:
            raise FileValidationError("File exceeds 10MB limit")
        detected = self._detect_mime(file_bytes, declared_type)
        if detected not in _ALLOWED:
            raise FileValidationError(f"Unsupported file type: {detected}")
        if detected == "application/pdf":
            try:
                import fitz
                if fitz.open(stream=file_bytes, filetype="pdf").page_count > MAX_PAGES:
                    raise FileValidationError("PDF exceeds 50 page limit")
            except ImportError:
                pass
        return detected

    @staticmethod
    def _detect_mime(file_bytes: bytes, declared: str) -> str:
        try:
            import magic
            return magic.from_buffer(file_bytes, mime=True)
        except Exception:
            if file_bytes.startswith(b"%PDF"):
                return "application/pdf"
            if file_bytes[:8] in {b"\x89PNG\r\n\x1a\n"}:
                return "image/png"
            if file_bytes[:3] == b"\xff\xd8\xff":
                return "image/jpeg"
            return declared or "text/plain"


file_validator = FileValidator()
