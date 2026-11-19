"""Professional DOCX export (Day 10)."""
from __future__ import annotations

import io
import re

from ..core.prompts import DISCLAIMER


class DocumentGenerator:
    def generate_docx(self, title, content, jurisdiction, doc_type, party_a="", party_b="") -> bytes:
        try:
            from docx import Document
            from docx.enum.text import WD_ALIGN_PARAGRAPH
            from docx.shared import Inches
        except ImportError:
            return (f"{title}\n\n{content}\n\n{DISCLAIMER}").encode("utf-8")

        doc = Document()
        for section in doc.sections:
            section.top_margin = section.bottom_margin = Inches(1)
            section.left_margin = section.right_margin = Inches(1)

        header = doc.sections[0].header.paragraphs[0]
        header.text = "DocuSense Africa — Legal Document"
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        h = doc.add_heading(title or doc_type, level=1)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph(f"Jurisdiction: {jurisdiction}")
        if party_a or party_b:
            doc.add_paragraph(f"Between {party_a or '—'} and {party_b or '—'}")

        for block in re.split(r"\n\s*\n", content):
            block = block.strip()
            if not block:
                continue
            if re.match(r"^(CLause|CLAUSE|\d+\.|[A-Z][A-Z ]{6,})$", block):
                doc.add_heading(block, level=2)
            else:
                doc.add_paragraph(block)

        table = doc.add_table(rows=3, cols=2)
        cells = [
            ("Party A", party_a), ("Party B", party_b), ("Date", "________________"),
        ]
        for row, (label, value) in zip(table.rows, cells):
            row.cells[0].text = label
            row.cells[1].text = value

        footer = doc.sections[0].footer.paragraphs[0]
        footer.text = DISCLAIMER
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()


doc_generator = DocumentGenerator()
