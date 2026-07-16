"""Lightweight lexical search over skill excerpts (no paid embeddings)."""

from __future__ import annotations

import math
import re
from collections import Counter

from book_skills_mcp.models import MatchResult, SearchHit, SkillPackage

_TOKEN = re.compile(r"[a-z0-9']+", re.I)
_STOP = frozenset(
    "a an the and or of to in for on with by from as is are was were be been being "
    "this that these those it its at if then than so such into about over under".split()
)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN.findall(text) if t.lower() not in _STOP and len(t) > 1]


def _score(query_tokens: list[str], doc_tokens: list[str], doc_text: str) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    q = Counter(query_tokens)
    d = Counter(doc_tokens)
    overlap = sum(min(q[t], d[t]) for t in q)
    if overlap == 0:
        # substring fallback for multi-word phrases
        joined = " ".join(query_tokens)
        if joined and joined in doc_text.lower():
            return 0.35
        return 0.0
    coverage = overlap / max(1, len(query_tokens))
    tf = overlap / max(1, math.sqrt(len(doc_tokens)))
    return coverage * 0.65 + min(1.0, tf) * 0.35


def search_library(
    packages: list[SkillPackage],
    query: str,
    book_id: str | None = None,
    limit: int = 8,
) -> list[SearchHit]:
    q_tokens = tokenize(query)
    hits: list[SearchHit] = []
    for pkg in packages:
        if book_id and pkg.card.id != book_id:
            continue
        for ex in pkg.excerpts:
            doc_tokens = tokenize(ex.text + " " + ex.title + " " + " ".join(ex.tags))
            score = _score(q_tokens, doc_tokens, ex.text)
            if score <= 0:
                continue
            snippet = ex.text.strip().replace("\n", " ")
            if len(snippet) > 320:
                snippet = snippet[:317] + "..."
            authors = ", ".join(pkg.card.authors) if pkg.card.authors else "Unknown"
            locator = ex.locator or "n/a"
            citation = f'"{ex.title or "Excerpt"}" — {pkg.card.title} ({authors}), {locator}'
            hits.append(
                SearchHit(
                    book_id=pkg.card.id,
                    excerpt_id=ex.id,
                    title=ex.title or pkg.card.title,
                    locator=ex.locator,
                    score=round(score, 4),
                    snippet=snippet,
                    citation=citation,
                )
            )
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[: max(1, min(limit, 25))]


def match_skills(packages: list[SkillPackage], task: str, limit: int = 5) -> list[MatchResult]:
    q_tokens = tokenize(task)
    results: list[MatchResult] = []
    for pkg in packages:
        c = pkg.card
        blob = " ".join(
            [
                c.name,
                c.title,
                c.when_to_use,
                c.when_not_to_use,
                c.summary,
                " ".join(c.domains),
                " ".join(c.tags),
                " ".join(p.name + " " + p.description for p in pkg.playbooks),
                " ".join(f.name + " " + f.description for f in pkg.frameworks),
            ]
        )
        score = _score(q_tokens, tokenize(blob), blob)
        # boost exact domain/tag hits
        for t in q_tokens:
            if t in {d.lower() for d in c.domains} or t in {x.lower() for x in c.tags}:
                score += 0.15
        if score <= 0:
            continue
        reason_bits = []
        if any(t in c.when_to_use.lower() for t in q_tokens):
            reason_bits.append("matches when_to_use")
        if pkg.playbooks and any(t in " ".join(p.name for p in pkg.playbooks).lower() for t in q_tokens):
            reason_bits.append("has relevant playbook")
        if pkg.frameworks and any(
            t in " ".join(f.name for f in pkg.frameworks).lower() for t in q_tokens
        ):
            reason_bits.append("has relevant framework")
        if not reason_bits:
            reason_bits.append("lexical match on skill card / content")
        results.append(
            MatchResult(
                book_id=c.id,
                name=c.name,
                level=c.level,
                score=round(min(score, 1.5), 4),
                reason="; ".join(reason_bits),
                when_to_use=c.when_to_use,
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return results[: max(1, min(limit, 15))]
