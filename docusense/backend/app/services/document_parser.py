"""Document parsing with OCR fallback (Day 6)."""
from __future__ import annotations

import io


class DocumentParser:
    SUPPORTED = {"application/pdf", "text/plain", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "image/jpeg", "image/png"}

    def parse(self, file_bytes: bytes, file_type: str, file_name: str = "") -> str:
        if file_type == "text/plain":
            return file_bytes.decode("utf-8", errors="replace")
        if file_type == "application/pdf":
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                text = "\n".join(page.get_text() for page in doc)
                if text.strip():
                    return text
            except ImportError:
                pass
            return self._ocr(file_bytes)
        if "wordprocessingml" in file_type:
            try:
                from docx import Document
                doc = Document(io.BytesIO(file_bytes))
                return "\n".join(p.text for p in doc.paragraphs)
            except ImportError:
                return ""
        if file_type.startswith("image/"):
            return self._ocr(file_bytes)
        return file_bytes.decode("utf-8", errors="replace")

    @staticmethod
    def _ocr(file_bytes: bytes) -> str:
        try:
            import pytesseract
            from PIL import Image
            return pytesseract.image_to_string(Image.open(io.BytesIO(file_bytes)))
        except Exception:
            return ""


document_parser = DocumentParser()
