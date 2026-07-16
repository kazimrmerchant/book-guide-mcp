"""Build skill packages from local files or URLs."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from slugify import slugify

from book_skills_mcp.models import (
    Curriculum,
    CurriculumConcept,
    Excerpt,
    Framework,
    FrameworkField,
    LicenseKind,
    Playbook,
    PlaybookStep,
    Rubric,
    RubricCriterion,
    SkillCard,
    SkillLevel,
    SkillPackage,
    TextGenre,
    TocEntry,
)
from book_skills_mcp.paths import default_uploads_dir, import_sandbox_roots
from book_skills_mcp.security import assert_public_http_url, resolve_under_roots
from book_skills_mcp.store import Library, validate_book_id

log = logging.getLogger("book_skills_mcp.builder")

_MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024
_MAX_EXCERPTS = 80
_CHUNK_WORDS = 220
_MAX_TEXT_CHARS = 2_000_000


def _word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def _chunk_paragraphs(text: str, target_words: int = _CHUNK_WORDS) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf: list[str] = []
    words = 0
    for p in paras:
        w = _word_count(p)
        if words + w > target_words and buf:
            chunks.append("\n\n".join(buf))
            buf = [p]
            words = w
        else:
            buf.append(p)
            words += w
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


def _cap_text(text: str, notes: list[str]) -> str:
    if len(text) > _MAX_TEXT_CHARS:
        notes.append(f"Text truncated to {_MAX_TEXT_CHARS} characters for safety.")
        return text[:_MAX_TEXT_CHARS]
    return text


def extract_text_from_path(path: Path) -> tuple[str, list[str]]:
    """Return (full_text, notes)."""
    suffix = path.suffix.lower()
    notes: list[str] = []
    if suffix in {".md", ".txt", ".markdown"}:
        return _cap_text(path.read_text(encoding="utf-8", errors="replace"), notes), notes
    if suffix == ".html" or suffix == ".htm":
        html = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return _cap_text(soup.get_text("\n", strip=True), notes), notes
    if suffix == ".epub":
        try:
            import ebooklib
            from ebooklib import epub
        except ImportError as exc:
            raise RuntimeError("ebooklib is required for EPUB import") from exc
        book = epub.read_epub(str(path))
        parts: list[str] = []
        for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
            soup = BeautifulSoup(item.get_content(), "lxml")
            parts.append(soup.get_text("\n", strip=True))
        return _cap_text("\n\n".join(parts), notes), notes
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise RuntimeError("pypdf is required for PDF import") from exc
        reader = PdfReader(str(path))
        parts = []
        for i, page in enumerate(reader.pages):
            t = page.extract_text() or ""
            if t.strip():
                parts.append(t)
            if i > 400:
                notes.append("PDF truncated after 400 pages for safety.")
                break
        notes.append("PDF extraction can be noisy; prefer EPUB or Markdown when possible.")
        return _cap_text("\n\n".join(parts), notes), notes
    raise ValueError(f"Unsupported file type: {suffix}. Use .md, .txt, .html, .epub, or .pdf.")


def fetch_url_to_uploads(url: str, uploads: Path | None = None) -> Path:
    assert_public_http_url(url)
    parsed = urlparse(url)
    host = (parsed.hostname or "download").lower()
    dest_dir = uploads or default_uploads_dir()
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = slugify(parsed.path.rsplit("/", 1)[-1] or host) or "download"
    # No automatic redirect following across hosts without re-check: limit redirects + re-validate
    with httpx.Client(
        follow_redirects=False,
        timeout=30.0,
        headers={"User-Agent": "book-guide-mcp/0.1 (+https://github.com/kazimrmerchant/book-guide-mcp)"},
    ) as client:
        current = url
        for _ in range(5):
            assert_public_http_url(current)
            resp = client.get(current)
            if resp.status_code in {301, 302, 303, 307, 308}:
                loc = resp.headers.get("location")
                if not loc:
                    raise ValueError("Redirect without Location header.")
                # Resolve relative redirects
                current = str(httpx.URL(current).join(loc))
                continue
            resp.raise_for_status()
            ctype = (resp.headers.get("content-type") or "").lower()
            if "html" in ctype:
                ext = ".html"
            elif "epub" in ctype:
                ext = ".epub"
            elif "pdf" in ctype:
                ext = ".pdf"
            elif "text/plain" in ctype or "markdown" in ctype:
                ext = ".txt"
            else:
                path_ext = Path(urlparse(current).path).suffix.lower()
                ext = (
                    path_ext
                    if path_ext in {".md", ".txt", ".html", ".htm", ".epub", ".pdf"}
                    else ".html"
                )
            content = resp.content
            if len(content) > _MAX_DOWNLOAD_BYTES:
                raise ValueError(f"Download exceeds {_MAX_DOWNLOAD_BYTES} bytes limit.")
            out = dest_dir / f"{name}{ext}"
            out.write_bytes(content)
            return out
        raise ValueError("Too many redirects while fetching URL.")


def _heading_toc(text: str) -> list[TocEntry]:
    toc: list[TocEntry] = []
    for i, line in enumerate(text.splitlines()):
        m = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        toc.append(
            TocEntry(
                id=f"ch_{len(toc)+1:03d}",
                title=title,
                level=level,
                locator=f"line:{i+1}",
                summary="",
            )
        )
        if len(toc) >= 40:
            break
    if not toc:
        toc.append(TocEntry(id="ch_001", title="Main text", level=1, locator="start"))
    return toc


def classify_genre(text: str, title: str = "") -> tuple[TextGenre, list[str], float]:
    """Heuristic genre for honest scaffolding (method vs narrative).

    Returns (genre, notes, method_score 0..1).
    """
    sample = (title + "\n" + text[:12000]).lower()
    method_hits = 0
    narrative_hits = 0
    method_cues = (
        "step",
        "method",
        "framework",
        "checklist",
        "how to",
        "procedure",
        "principle",
        "definition",
        "chapter",
        "exercise",
        "practice",
        "guideline",
        "protocol",
        "you should",
        "first,",
        "second,",
        "warning",
        "do not",
        "rubric",
    )
    narrative_cues = (
        "once upon",
        "he said",
        "she said",
        "they said",
        "chapter 1",
        "novel",
        "protagonist",
        "whispered",
        "suddenly",
        "love story",
        "kingdom",
        "dragon",
        "murder",
        "detective",
    )
    for cue in method_cues:
        method_hits += sample.count(cue)
    for cue in narrative_cues:
        narrative_hits += sample.count(cue)
    # Imperative density rough signal
    imperatives = len(re.findall(r"\b(do|use|apply|define|list|write|ask|check|verify)\b", sample))
    method_hits += min(imperatives, 20)
    notes: list[str] = []
    total = method_hits + narrative_hits + 1
    method_score = method_hits / total
    if method_hits >= narrative_hits + 3 and method_hits >= 4:
        genre = TextGenre.METHOD
        notes.append(f"Genre=method (method cues={method_hits}, narrative={narrative_hits}).")
    elif narrative_hits >= method_hits + 2 and narrative_hits >= 3:
        genre = TextGenre.NARRATIVE
        notes.append(
            f"Genre=narrative (method cues={method_hits}, narrative={narrative_hits}). "
            "Scaffolding limited to L0–L1 (search/cite + guide card); weak auto-playbooks omitted."
        )
    elif method_hits >= 2 and narrative_hits >= 2:
        genre = TextGenre.MIXED
        notes.append(f"Genre=mixed (method={method_hits}, narrative={narrative_hits}).")
    else:
        genre = TextGenre.UNKNOWN
        notes.append("Genre=unknown; defaulting to cautious method scaffolding.")
    return genre, notes, round(method_score, 3)


def _auto_playbook(title: str, book_id: str, genre: TextGenre = TextGenre.UNKNOWN) -> Playbook | None:
    if genre == TextGenre.NARRATIVE:
        return None  # honest: novels are not procedure handbooks
    return Playbook(
        id="guided-study",
        name="Guided study pass",
        description=f"A generic L2 study playbook auto-generated for {title}.",
        steps=[
            PlaybookStep(
                id="orient",
                title="Orient",
                instruction="State your goal with this book and which chapter or idea you will use.",
                questions=["What problem are you solving?", "Which section seems most relevant?"],
                success_criteria=["Clear goal in one sentence", "One target section identified"],
            ),
            PlaybookStep(
                id="extract",
                title="Extract method",
                instruction="From the relevant excerpts, list the author's method as numbered steps.",
                questions=["What does the author tell you to *do*?", "What do they warn against?"],
                success_criteria=["3–7 actionable steps", "At least one caution noted"],
            ),
            PlaybookStep(
                id="apply",
                title="Apply",
                instruction="Apply the method to your live task. Write the draft output.",
                questions=["What changed in your plan after applying the method?"],
                success_criteria=["Concrete artifact produced", "Citation to an excerpt"],
            ),
            PlaybookStep(
                id="transfer",
                title="Transfer (fresh particular)",
                instruction=(
                    "Apply the same method to a *new* case not used above "
                    "(different project, person, or constraint)."
                ),
                questions=[
                    "What is the fresh particular?",
                    "Which clause of the method still holds? What breaks?",
                ],
                success_criteria=["Second concrete case", "Note on transfer vs memorization"],
            ),
            PlaybookStep(
                id="reflect",
                title="Reflect",
                instruction="Score yourself against the book's standards and name one next experiment.",
                questions=["Where did you diverge from the book?", "What will you try next?"],
                success_criteria=["Honest gap analysis", "One next experiment"],
            ),
        ],
        estimated_minutes=55,
    )


def _auto_framework(title: str, genre: TextGenre = TextGenre.UNKNOWN) -> Framework | None:
    if genre == TextGenre.NARRATIVE:
        return Framework(
            id="theme-lens",
            name="Theme / motif lens",
            description=(
                f"Literary reading lens for {title} (narrative genre). "
                "Not a procedure handbook — themes, motifs, character claims."
            ),
            fields=[
                FrameworkField(name="subject", description="Passage, character, or theme under examination."),
                FrameworkField(name="claim", description="One defendable claim about the text."),
                FrameworkField(name="evidence", description="Quoted or located support from excerpts."),
                FrameworkField(
                    name="counter_reading",
                    description="Strongest alternative interpretation.",
                    required=False,
                ),
                FrameworkField(name="citations", description="Excerpt ids / locators.", required=False),
            ],
            process=[
                "State one claim (not a vibe).",
                "Support with located evidence.",
                "Steelman a counter-reading.",
            ],
            output_shape="subject → claim → evidence → counter_reading → citations",
        )
    return Framework(
        id="book-lens",
        name="Book lens review",
        description=f"Apply {title} as a structured review lens.",
        fields=[
            FrameworkField(name="context", description="What is being reviewed or decided."),
            FrameworkField(name="book_principles", description="2–5 principles from the book."),
            FrameworkField(name="diagnosis", description="How the context looks through those principles."),
            FrameworkField(name="recommendations", description="Actions the book would recommend."),
            FrameworkField(
                name="citations",
                description="Excerpt IDs or locators supporting the recommendations.",
                required=False,
            ),
            FrameworkField(
                name="fresh_particular",
                description="A second, different case to test transfer (not the same example).",
                required=False,
            ),
        ],
        process=[
            "Search the skill for principles matching the context.",
            "Map each principle to a diagnosis.",
            "Propose recommendations with citations.",
            "Transfer: apply to one fresh particular.",
            "List open questions the book does not settle.",
        ],
        output_shape="context → principles → diagnosis → recommendations → fresh_particular → citations",
    )


def _auto_rubric(title: str) -> Rubric:
    return Rubric(
        id="book-fidelity",
        name="Book-fidelity application",
        description=f"Grade how faithfully work applies {title}.",
        criteria=[
            RubricCriterion(
                id="principles",
                name="Principles used",
                description="Uses named ideas from the book rather than generic advice.",
                weight=1.2,
            ),
            RubricCriterion(
                id="procedure",
                name="Procedure",
                description="Follows a book-like sequence or playbook when one exists.",
                weight=1.0,
            ),
            RubricCriterion(
                id="evidence",
                name="Evidence",
                description="Cites locators / excerpts instead of inventing quotes.",
                weight=1.3,
            ),
            RubricCriterion(
                id="limits",
                name="Limits & humility",
                description="Notes where the book is silent or contested.",
                weight=0.8,
            ),
        ],
        pass_threshold=0.7,
    )


def _auto_curriculum(book_id: str, toc: list[TocEntry], excerpts: list[Excerpt]) -> Curriculum:
    concepts: list[CurriculumConcept] = []
    for i, ch in enumerate(toc[:12]):
        related = [e.id for e in excerpts if e.chapter_id == ch.id][:3]
        if not related and excerpts:
            related = [excerpts[min(i, len(excerpts) - 1)].id]
        concepts.append(
            CurriculumConcept(
                id=f"concept_{i+1:03d}",
                name=ch.title,
                summary=f"Core idea cluster for: {ch.title}",
                chapter_id=ch.id,
                prerequisites=[f"concept_{i:03d}"] if i > 0 else [],
                key_questions=[
                    f"What problem does '{ch.title}' address?",
                    f"How would you apply '{ch.title}' to a live case?",
                    f"What is a common misunderstanding of '{ch.title}'?",
                ],
                misconceptions=[
                    f"Treating '{ch.title}' as a slogan instead of a method.",
                ],
                excerpt_ids=related,
            )
        )
    path = [c.id for c in concepts]
    return Curriculum(book_id=book_id, concepts=concepts, learning_paths=[path] if path else [])


def build_skill_from_text(
    *,
    text: str,
    title: str,
    authors: list[str] | None = None,
    book_id: str | None = None,
    license_kind: LicenseKind = LicenseKind.USER_OWNED,
    license_note: str = "",
    sources: list[str] | None = None,
    domains: list[str] | None = None,
    when_to_use: str | None = None,
    full_text_allowed: bool = False,
    builder_notes: list[str] | None = None,
) -> SkillPackage:
    bid = validate_book_id(book_id or slugify(title)[:48] or "book")
    genre, genre_notes, method_score = classify_genre(text, title)
    toc = _heading_toc(text)
    chunks = _chunk_paragraphs(text)
    excerpts: list[Excerpt] = []
    for i, chunk in enumerate(chunks[:_MAX_EXCERPTS]):
        ch = toc[min(i * len(toc) // max(1, len(chunks)), len(toc) - 1)]
        excerpts.append(
            Excerpt(
                id=f"ex_{i+1:04d}",
                chapter_id=ch.id,
                title=ch.title if i < len(toc) else f"Passage {i+1}",
                text=chunk.strip(),
                locator=f"chunk:{i+1}",
                words=_word_count(chunk),
                tags=domains or [],
            )
        )
    authors = authors or []
    domains = domains or ["general"]
    if genre == TextGenre.NARRATIVE:
        level = SkillLevel.L1_GUIDE
        default_when = (
            f"Use when discussing themes, characters, or claims *from* '{title}' "
            f"with citations — not as a how-to procedure handbook."
        )
        default_not = (
            "Do not treat narrative prose as operational SOPs. "
            "Do not use for medical, legal, or emergency decisions. "
            "Do not reproduce large copyrighted passages."
        )
        tags = domains + ["book-skill", "narrative", "genre-narrative"]
    else:
        level = SkillLevel.L4_MENTOR
        default_when = (
            f"Use when the agent should apply methods, frameworks, or teaching from "
            f"'{title}' rather than generic advice. Not a raw RAG dump."
        )
        default_not = (
            "Do not use for medical, legal, or emergency decisions as a substitute for professionals. "
            "Do not reproduce large copyrighted passages. "
            "Do not claim this is only retrieval if playbooks/frameworks are available."
        )
        tags = domains + ["book-skill", f"genre-{genre.value}"]

    card = SkillCard(
        id=bid,
        name=bid,
        title=title,
        authors=authors,
        level=level,
        when_to_use=when_to_use or default_when,
        when_not_to_use=default_not,
        domains=domains,
        summary=(
            f"Skill package built from '{title}' "
            f"(genre={genre.value}, method_score={method_score})."
        ),
        license=license_kind,
        license_note=license_note
        or (
            "User-owned: you attested you have rights to use this copy for personal agent tooling."
            if license_kind == LicenseKind.USER_OWNED
            else ""
        ),
        sources=sources or [],
        safety_notes=[
            "Prefer citations over paraphrase-as-quote.",
            "Historical scientific claims may be outdated; verify against modern sources.",
            "Host model supplies prose; this MCP supplies methods, evidence, and session moves.",
        ],
        tags=tags,
    )
    playbooks: list[Playbook] = []
    pb = _auto_playbook(title, bid, genre)
    if pb:
        playbooks.append(pb)
    frameworks: list[Framework] = []
    fw = _auto_framework(title, genre)
    if fw:
        frameworks.append(fw)
    # Narrative: still allow thin curriculum for discussion, but L1 effective level
    curriculum = None if genre == TextGenre.NARRATIVE else _auto_curriculum(bid, toc, excerpts)
    notes = list(builder_notes or []) + genre_notes
    pkg = SkillPackage(
        card=card,
        toc=toc,
        excerpts=excerpts,
        playbooks=playbooks,
        frameworks=frameworks,
        rubrics=[_auto_rubric(title)] if genre != TextGenre.NARRATIVE else [],
        curriculum=curriculum,
        genre=genre,
        full_text_allowed=full_text_allowed and license_kind in {
            LicenseKind.PUBLIC_DOMAIN,
            LicenseKind.OPEN_LICENSE,
        },
        builder_notes=notes,
    )
    # Align declared level with genre honesty
    pkg.card.level = pkg.effective_level()
    return pkg


def import_file(
    library: Library,
    path: str | Path,
    *,
    title: str | None = None,
    authors: list[str] | None = None,
    book_id: str | None = None,
    license_kind: LicenseKind = LicenseKind.USER_OWNED,
    ownership_attested: bool = False,
    domains: list[str] | None = None,
    sandbox_roots: list[Path] | None = None,
) -> SkillPackage:
    roots = sandbox_roots if sandbox_roots is not None else import_sandbox_roots()
    p = resolve_under_roots(path, roots)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(
            f"File not found under sandbox: {p}. "
            "Copy the book into data/uploads/ or set BOOK_EXTRA_IMPORT_ROOT / BOOK_IMPORT_ROOTS."
        )
    if license_kind == LicenseKind.USER_OWNED and not ownership_attested:
        raise ValueError(
            "For user_owned imports set ownership_attested=true to confirm you own a legal copy."
        )
    text, notes = extract_text_from_path(p)
    if _word_count(text) < 40:
        raise ValueError("Extracted text too short to build a skill. Check the file.")
    pkg = build_skill_from_text(
        text=text,
        title=title or p.stem.replace("_", " ").replace("-", " ").title(),
        authors=authors,
        book_id=book_id,
        license_kind=license_kind,
        sources=[str(p)],
        domains=domains,
        full_text_allowed=license_kind == LicenseKind.PUBLIC_DOMAIN,
        builder_notes=notes,
    )
    library.save_package(pkg)
    return pkg


def import_url(
    library: Library,
    url: str,
    *,
    title: str | None = None,
    authors: list[str] | None = None,
    book_id: str | None = None,
    license_kind: LicenseKind = LicenseKind.UNKNOWN,
    ownership_attested: bool = False,
    domains: list[str] | None = None,
) -> SkillPackage:
    if license_kind == LicenseKind.USER_OWNED and not ownership_attested:
        raise ValueError(
            "For user_owned URL imports set ownership_attested=true to confirm legal rights."
        )
    if license_kind == LicenseKind.UNKNOWN:
        # Public domain hosts get a soft default; still not full_text unless explicit
        host = (urlparse(url).hostname or "").lower()
        if any(h in host for h in ("gutenberg.org", "archive.org", "wikisource.org")):
            license_kind = LicenseKind.PUBLIC_DOMAIN
    path = fetch_url_to_uploads(url)
    text, notes = extract_text_from_path(path)
    notes = list(notes) + [f"Fetched from {url}"]
    if _word_count(text) < 40:
        raise ValueError("Fetched content too short. The URL may require JS or login.")
    pkg = build_skill_from_text(
        text=text,
        title=title or path.stem.replace("_", " ").replace("-", " ").title(),
        authors=authors,
        book_id=book_id,
        license_kind=license_kind,
        sources=[url, str(path)],
        domains=domains,
        full_text_allowed=license_kind == LicenseKind.PUBLIC_DOMAIN,
        builder_notes=notes,
    )
    library.save_package(pkg)
    return pkg
