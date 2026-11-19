"""Seed law_chunks from Laws.Africa (Day 7).

Usage: python seed_laws.py --countries NG,GH,KE | --all
"""
from __future__ import annotations

import argparse
import asyncio
import re

from app.core.sanitizer import parse_xml_safely
from app.services.embedder import embedder

FALLBACK_CONSTITUTIONS = {
    "NG": "1999 Constitution of the Federal Republic of Nigeria: fundamental rights, "
          "federal structure, and the supremacy of the constitution.",
    "GH": "1992 Constitution of Ghana: fundamental human rights and freedoms, "
          "the presidency, parliament and the judiciary.",
    "KE": "2010 Constitution of Kenya: Bill of Rights, devolution, and separation of powers.",
    "ZA": "Constitution of the Republic of South Africa, 1996: Bill of Rights and constitutional supremacy.",
}

_CONF = FALLBACK_CONSTITUTIONS


async def _fetch_country(country: str, token: str) -> list[dict]:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(
                f"https://api.laws.africa/v3/akn/{country}/.json",
                headers={"Authorization": f"Token {token}"} if token else {},
            )
            if r.status_code != 200:
                return []
            results = r.json().get("results", [])
            docs = []
            for item in results[:40]:
                html = await client.get(item.get("html_url", ""), timeout=30)
                text = re.sub(r"<[^>]+>", " ", html.text)
                docs.append({"title": item.get("title", country),
                             "content": re.sub(r"\s+", " ", text).strip()})
            return docs
    except Exception:
        return []


async def seed(countries: list[str], token: str) -> None:
    from app.models.database import get_engine
    from sqlalchemy import text
    engine = get_engine()
    for country in countries:
        docs = await _fetch_country(country, token)
        if not docs and country in _CONF:
            docs = [{"title": f"{country} Constitution", "content": _CONF[country]}]
        chunks, vectors = embedder.embed_document_for_rag("\n\n".join(d["content"] for d in docs))
        inserted = 0
        if engine is not None and chunks:
            with engine.begin() as conn:
                existing = conn.execute(text("SELECT COUNT(*) FROM law_chunks WHERE country=:c"), {"c": country}).scalar()
                if (existing or 0) > 100:
                    print(f"{country}: already seeded ({existing} chunks)")
                    continue
                for chunk, vector in zip(chunks, vectors):
                    conn.execute(text(
                        "INSERT INTO law_chunks (id, country, law_type, law_title, section, "
                        "content, embedding, seeded_at) VALUES (uuid_generate_v4(), :c, "
                        "'constitution', :t, 'General', :content, :vec, NOW())"
                    ), {"c": country, "t": docs[0]["title"], "content": chunk, "vec": str(vector)})
                    inserted += 1
        print(f"{country}: {len(docs)} acts, {inserted or len(chunks)} chunks seeded")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--countries", default="")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()
    from app.core.config import settings
    codes = ([c.strip().upper() for c in args.countries.split(",") if c.strip()]
             if args.countries else (["NG", "GH", "KE", "ZA", "US", "GB", "FR"] if args.all else ["NG"]))
    asyncio.run(seed(codes, settings.laws_africa_token))
