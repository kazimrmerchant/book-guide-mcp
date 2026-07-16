"""Load / save skill packages and session state."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from book_skills_mcp.models import (
    Curriculum,
    Excerpt,
    Framework,
    Playbook,
    PlaybookSession,
    Rubric,
    SkillCard,
    SkillPackage,
    TextGenre,
    TocEntry,
    TutorSession,
)
from book_skills_mcp.paths import (
    default_library_dir,
    default_sessions_dir,
    default_skills_dir,
    package_root,
)

log = logging.getLogger("book_skills_mcp.store")

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_optional_list(path: Path, model_cls: type) -> list:
    if not path.exists():
        return []
    raw = _read_json(path)
    if not isinstance(raw, list):
        return []
    return [model_cls.model_validate(item) for item in raw]


def load_skill_dir(skill_dir: Path) -> SkillPackage | None:
    card_path = skill_dir / "skill.json"
    if not card_path.exists():
        # SKILL.md-only packages: minimal card from frontmatter-like skill.md json twin
        alt = skill_dir / "card.json"
        if not alt.exists():
            return None
        card_path = alt
    try:
        card = SkillCard.model_validate(_read_json(card_path))
        toc = _load_optional_list(skill_dir / "toc.json", TocEntry)
        excerpts = _load_optional_list(skill_dir / "excerpts" / "index.json", Excerpt)
        if not excerpts and (skill_dir / "excerpts.json").exists():
            excerpts = _load_optional_list(skill_dir / "excerpts.json", Excerpt)
        playbooks = _load_optional_list(skill_dir / "playbooks" / "index.json", Playbook)
        if not playbooks:
            playbooks = [
                Playbook.model_validate(_read_json(p))
                for p in sorted((skill_dir / "playbooks").glob("*.json"))
                if p.name != "index.json"
            ]
        frameworks = _load_optional_list(skill_dir / "frameworks" / "index.json", Framework)
        if not frameworks:
            frameworks = [
                Framework.model_validate(_read_json(p))
                for p in sorted((skill_dir / "frameworks").glob("*.json"))
                if p.name != "index.json"
            ]
        rubrics = _load_optional_list(skill_dir / "rubrics" / "index.json", Rubric)
        if not rubrics:
            rubrics = [
                Rubric.model_validate(_read_json(p))
                for p in sorted((skill_dir / "rubrics").glob("*.json"))
                if p.name != "index.json"
            ]
        curriculum = None
        cur_path = skill_dir / "curriculum" / "curriculum.json"
        if cur_path.exists():
            curriculum = Curriculum.model_validate(_read_json(cur_path))
        full_text_allowed = False
        rights = skill_dir / "RIGHTS.md"
        if rights.exists() and "full_text_allowed: true" in rights.read_text(encoding="utf-8").lower():
            full_text_allowed = True
        genre = TextGenre.UNKNOWN
        meta_notes: list[str] = []
        meta_path = skill_dir / "meta.json"
        if meta_path.exists():
            try:
                meta = _read_json(meta_path)
                if isinstance(meta, dict):
                    if meta.get("genre"):
                        genre = TextGenre(str(meta["genre"]))
                    notes = meta.get("builder_notes")
                    if isinstance(notes, list):
                        meta_notes = [str(n) for n in notes]
            except Exception:  # noqa: BLE001
                genre = TextGenre.UNKNOWN
        # Infer method genre for curated demo skills
        if genre == TextGenre.UNKNOWN and (
            "method" in " ".join(card.tags).lower()
            or "socratic" in card.id
            or "avicenna" in card.id
        ):
            genre = TextGenre.METHOD
        pkg = SkillPackage(
            card=card,
            toc=toc,
            excerpts=excerpts,
            playbooks=playbooks,
            frameworks=frameworks,
            rubrics=rubrics,
            curriculum=curriculum,
            genre=genre,
            full_text_allowed=full_text_allowed,
            builder_notes=meta_notes,
        )
        order = ["L0", "L1", "L2", "L3", "L4"]
        inferred = pkg.effective_level()
        # Curated method demos keep declared L4; narrative imports are capped by effective_level
        if genre == TextGenre.NARRATIVE:
            pkg.card.level = inferred
        else:
            best = max(order.index(card.level.value), order.index(inferred.value))
            pkg.card.level = type(card.level)(order[best])
        return pkg
    except Exception as exc:  # noqa: BLE001 — surface bad packages, don't crash server
        log.exception("Failed to load skill at %s: %s", skill_dir, exc)
        return None


class Library:
    """In-memory index of skill packages on disk."""

    def __init__(
        self,
        skills_dir: Path | None = None,
        library_dir: Path | None = None,
        sessions_dir: Path | None = None,
        extra_skill_dirs: list[Path] | None = None,
    ) -> None:
        self.skills_dir = skills_dir or default_skills_dir()
        self.library_dir = library_dir or default_library_dir()
        self.sessions_dir = sessions_dir or default_sessions_dir()
        self.extra_skill_dirs = list(extra_skill_dirs or [])
        # Dev convenience: also scan repo-level ./skills if distinct from packaged bundle
        dev_skills = package_root() / "skills"
        if dev_skills.is_dir() and dev_skills.resolve() != self.skills_dir.resolve():
            if dev_skills not in self.extra_skill_dirs:
                self.extra_skill_dirs.append(dev_skills)
        self.library_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._packages: dict[str, SkillPackage] = {}
        self._paths: dict[str, Path] = {}
        self.reload()

    def reload(self) -> int:
        self._packages.clear()
        self._paths.clear()
        count = 0
        # Order: bundled/skills first, then extras, then user library (user overrides ids)
        bases: list[Path] = [self.skills_dir, *self.extra_skill_dirs, self.library_dir]
        seen_bases: set[str] = set()
        for base in bases:
            key = str(base.resolve()) if base.exists() else str(base)
            if key in seen_bases:
                continue
            seen_bases.add(key)
            if not base.exists():
                continue
            for child in sorted(base.iterdir()):
                if not child.is_dir() or child.name.startswith("."):
                    continue
                pkg = load_skill_dir(child)
                if pkg is None:
                    continue
                self._packages[pkg.card.id] = pkg
                self._paths[pkg.card.id] = child
                count += 1
        log.info("Loaded %s skill packages from %s roots", count, len(seen_bases))
        return count

    def list_packages(self) -> list[SkillPackage]:
        return list(self._packages.values())

    def get(self, book_id: str) -> SkillPackage | None:
        return self._packages.get(book_id)

    def path_for(self, book_id: str) -> Path | None:
        return self._paths.get(book_id)

    def register(self, pkg: SkillPackage, path: Path) -> None:
        self._packages[pkg.card.id] = pkg
        self._paths[pkg.card.id] = path

    def save_package(self, pkg: SkillPackage, dest: Path | None = None) -> Path:
        path = dest or (self.library_dir / pkg.card.id)
        path.mkdir(parents=True, exist_ok=True)
        (path / "playbooks").mkdir(exist_ok=True)
        (path / "frameworks").mkdir(exist_ok=True)
        (path / "rubrics").mkdir(exist_ok=True)
        (path / "excerpts").mkdir(exist_ok=True)
        (path / "curriculum").mkdir(exist_ok=True)

        _write_json(path / "skill.json", pkg.card.model_dump(mode="json"))
        _write_json(
            path / "meta.json",
            {
                "genre": pkg.genre.value,
                "effective_level": pkg.effective_level().value,
                "builder_notes": pkg.builder_notes,
            },
        )
        _write_json(path / "toc.json", [t.model_dump(mode="json") for t in pkg.toc])
        _write_json(
            path / "excerpts" / "index.json",
            [e.model_dump(mode="json") for e in pkg.excerpts],
        )
        _write_json(
            path / "playbooks" / "index.json",
            [p.model_dump(mode="json") for p in pkg.playbooks],
        )
        _write_json(
            path / "frameworks" / "index.json",
            [f.model_dump(mode="json") for f in pkg.frameworks],
        )
        _write_json(
            path / "rubrics" / "index.json",
            [r.model_dump(mode="json") for r in pkg.rubrics],
        )
        if pkg.curriculum:
            _write_json(
                path / "curriculum" / "curriculum.json",
                pkg.curriculum.model_dump(mode="json"),
            )
        rights = [
            f"# Rights — {pkg.card.title}",
            "",
            f"license: {pkg.card.license.value}",
            f"full_text_allowed: {'true' if pkg.full_text_allowed else 'false'}",
            "",
            pkg.card.license_note or "See package metadata.",
            "",
        ]
        (path / "RIGHTS.md").write_text("\n".join(rights), encoding="utf-8")
        skill_md = _render_skill_md(pkg)
        (path / "SKILL.md").write_text(skill_md, encoding="utf-8")
        self.register(pkg, path)
        return path

    # --- sessions ------------------------------------------------------------

    def _session_path(self, kind: str, session_id: str) -> Path:
        return self.sessions_dir / kind / f"{session_id}.json"

    def save_playbook_session(self, session: PlaybookSession) -> None:
        session.updated_at = _now()
        _write_json(
            self._session_path("playbook", session.session_id),
            session.model_dump(mode="json"),
        )

    def load_playbook_session(self, session_id: str) -> PlaybookSession | None:
        path = self._session_path("playbook", session_id)
        if not path.exists():
            return None
        return PlaybookSession.model_validate(_read_json(path))

    def save_tutor_session(self, session: TutorSession) -> None:
        session.updated_at = _now()
        _write_json(
            self._session_path("tutor", session.session_id),
            session.model_dump(mode="json"),
        )

    def load_tutor_session(self, session_id: str) -> TutorSession | None:
        path = self._session_path("tutor", session_id)
        if not path.exists():
            return None
        return TutorSession.model_validate(_read_json(path))

    def new_id(self, prefix: str = "s") -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _render_skill_md(pkg: SkillPackage) -> str:
    c = pkg.card
    lines = [
        "---",
        f"name: {c.id}",
        f"title: {c.title}",
        f"level: {c.level.value}",
        f"license: {c.license.value}",
        f"when_to_use: |",
        f"  {c.when_to_use.replace(chr(10), chr(10) + '  ')}",
        "---",
        "",
        f"# {c.title}",
        "",
        c.summary or c.when_to_use,
        "",
        "## When to use",
        "",
        c.when_to_use,
        "",
    ]
    if c.when_not_to_use:
        lines += ["## When not to use", "", c.when_not_to_use, ""]
    if pkg.playbooks:
        lines += ["## Playbooks", ""]
        for p in pkg.playbooks:
            lines.append(f"- `{p.id}` — {p.name}: {p.description}")
        lines.append("")
    if pkg.frameworks:
        lines += ["## Frameworks", ""]
        for f in pkg.frameworks:
            lines.append(f"- `{f.id}` — {f.name}: {f.description}")
        lines.append("")
    if c.safety_notes:
        lines += ["## Safety", ""]
        for n in c.safety_notes:
            lines.append(f"- {n}")
        lines.append("")
    return "\n".join(lines)


def validate_book_id(book_id: str) -> str:
    bid = book_id.strip().lower().replace(" ", "-")
    if not _ID_RE.match(bid):
        raise ValueError(
            f"Invalid book_id '{book_id}'. Use lowercase letters, digits, _ or - (max 64)."
        )
    return bid
