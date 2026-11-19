"""pgvector RAG retrieval and law-context formatting (Day 7)."""
from __future__ import annotations

from .embedder import embedder


class LawRetriever:
    def retrieve(self, query: str, country: str, db=None, top_k: int = 6) -> list[dict]:
        vector = embedder.embed_query(query)
        if db is None:
            return []
        try:
            from sqlalchemy import text
            rows = db.execute(
                text("SELECT law_title, section, content, source_url, "
                     "(embedding <=> :vec) AS distance FROM law_chunks "
                     "WHERE country = :country ORDER BY distance LIMIT :top_k"),
                {"vec": str(vector), "country": country, "top_k": top_k},
            ).fetchall()
            return [
                {
                    "title": r[0], "section": r[1], "content": r[2],
                    "similarity": 1 - float(r[4] or 0), "source_url": r[3],
                }
                for r in rows
            ]
        except Exception:
            return []

    def retrieve_for_document(self, doc_text: str, country: str, db=None) -> str:
        chunks = self.retrieve(doc_text[:500], country, db)
        if not chunks:
            return "RELEVANT LAW:\n(no indexed law chunks available for this jurisdiction)\n"
        body = "\n\n".join(
            f"[{c['title']} - {c['section']}]\n{c['content']}" for c in chunks
        )
        return f"RELEVANT LAW:\n{body}\n"


law_retriever = LawRetriever()
