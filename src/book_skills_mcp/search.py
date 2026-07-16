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


# Intent keywords → boost matching demo / method skills
_INTENT_BOOSTS: dict[str, tuple[str, ...]] = {
    "socratic": ("socratic", "elenchus", "dialectic", "question", "quiz", "dialogue"),
    "avicenna": ("avicenna", "ibn", "sina", "hadd", "burhan", "definition", "canon"),
    "tutor": ("tutor", "teach", "mentor", "coach", "curriculum", "mastery"),
    "playbook": ("playbook", "procedure", "steps", "checklist"),
    "framework": ("framework", "method", "lens", "rubric", "review"),
    "cite": ("cite", "citation", "quote", "evidence", "passage"),
}


def match_skills(packages: list[SkillPackage], task: str, limit: int = 5) -> list[MatchResult]:
    q_tokens = tokenize(task)
    task_l = task.lower()
    results: list[MatchResult] = []
    for pkg in packages:
        c = pkg.card
        excerpt_sample = " ".join(
            (e.title + " " + e.text[:160]) for e in pkg.excerpts[:12]
        )
        concept_sample = ""
        if pkg.curriculum:
            concept_sample = " ".join(
                x.name + " " + x.summary for x in pkg.curriculum.concepts[:12]
            )
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
                " ".join(r.name + " " + r.description for r in pkg.rubrics),
                excerpt_sample,
                concept_sample,
            ]
        )
        score = _score(q_tokens, tokenize(blob), blob)
        # boost exact domain/tag/id hits
        id_bits = {c.id.lower(), c.name.lower(), *{d.lower() for d in c.domains}, *{x.lower() for x in c.tags}}
        for t in q_tokens:
            if t in id_bits or t in c.id.lower().replace("-", " ").split():
                score += 0.2
        # intent boosts (Socratic/Avicenna tutors, etc.)
        reason_bits: list[str] = []
        for label, keys in _INTENT_BOOSTS.items():
            if any(k in task_l for k in keys):
                skill_blob = (c.id + " " + c.title + " " + " ".join(c.tags) + " " + c.when_to_use).lower()
                if any(k in skill_blob for k in keys) or label in skill_blob:
                    score += 0.35
                    reason_bits.append(f"intent:{label}")
        if any(t in c.when_to_use.lower() for t in q_tokens):
            reason_bits.append("matches when_to_use")
        if pkg.playbooks and any(t in " ".join(p.name for p in pkg.playbooks).lower() for t in q_tokens):
            reason_bits.append("has relevant playbook")
        if pkg.frameworks and any(
            t in " ".join(f.name for f in pkg.frameworks).lower() for t in q_tokens
        ):
            reason_bits.append("has relevant framework")
        if pkg.curriculum and any(t in concept_sample.lower() for t in q_tokens):
            reason_bits.append("matches curriculum concepts")
        if score <= 0:
            continue
        if not reason_bits:
            reason_bits.append("lexical match on skill card / content")
        results.append(
            MatchResult(
                book_id=c.id,
                name=c.name,
                level=c.level,
                score=round(min(score, 2.0), 4),
                reason="; ".join(reason_bits),
                when_to_use=c.when_to_use,
            )
        )
    results.sort(key=lambda r: r.score, reverse=True)
    return results[: max(1, min(limit, 15))]
