"""Cohere embeddings and document chunking (Day 6)."""
from __future__ import annotations

import time

from ..core.config import settings

BATCH_SIZE = 96
DIMENSION = 1024


class Embedder:
    def embed(self, texts: list[str], *, input_type: str = "search_document") -> list[list[float]]:
        if not texts:
            return []
        try:
            import cohere
            client = cohere.Client(settings.cohere_api_key or "dev")
            result = []
            for i in range(0, len(texts), BATCH_SIZE):
                batch = texts[i:i + BATCH_SIZE]
                for attempt in range(3):
                    try:
                        response = client.embed(
                            texts=batch, model="embed-english-v3.0",
                            input_type=input_type, truncate="END",
                        )
                        result.extend([list(map(float, v)) for v in response.embeddings])
                        break
                    except Exception:
                        if attempt == 2:
                            raise
                        time.sleep(0.5 * (attempt + 1))
            return result
        except Exception:
            # Deterministic offline fallback keeps the app usable without an API key.
            return [self._fallback(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query], input_type="search_query")[0]

    def embed_document_for_rag(self, text: str) -> tuple[list[str], list[list[float]]]:
        try:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
            chunks = splitter.split_text(text)
        except ImportError:
            chunks = [text[i:i + 800] for i in range(0, len(text), 650)]
        return chunks, self.embed(chunks)

    @staticmethod
    def _fallback(text: str) -> list[float]:
        vec = [0.0] * DIMENSION
        for i, ch in enumerate(text.lower()):
            vec[ord(ch) % DIMENSION] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]


embedder = Embedder()
