from __future__ import annotations

from pathlib import Path

from book_skills_mcp.builder import build_skill_from_text, import_file
from book_skills_mcp.models import LicenseKind, TutorMode
from book_skills_mcp.playbooks import apply_framework, start_playbook
from book_skills_mcp.search import match_skills, search_library
from book_skills_mcp.store import Library
from book_skills_mcp.tutor import record_mastery, start_tutor, tutor_turn


ROOT = Path(__file__).resolve().parents[1]


def test_bundled_skills_load():
    lib = Library(skills_dir=ROOT / "skills", library_dir=ROOT / "library")
    ids = {p.card.id for p in lib.list_packages()}
    assert "avicenna-canon" in ids
    assert "socratic-method" in ids
    avi = lib.get("avicenna-canon")
    assert avi is not None
    assert avi.curriculum and len(avi.curriculum.concepts) >= 5
    assert avi.playbooks and avi.frameworks and avi.rubrics


def test_search_and_match():
    lib = Library(skills_dir=ROOT / "skills", library_dir=ROOT / "library")
    hits = search_library(lib.list_packages(), "definition genus differentia", book_id="avicenna-canon")
    assert hits
    assert hits[0].book_id == "avicenna-canon"
    matches = match_skills(lib.list_packages(), "teach with socratic questions")
    assert matches
    assert any(m.book_id == "socratic-method" for m in matches)


def test_socratic_tutor_session(tmp_path: Path):
    lib = Library(
        skills_dir=ROOT / "skills",
        library_dir=tmp_path / "library",
        sessions_dir=tmp_path / "sessions",
    )
    started = start_tutor(lib, "socratic-method", mode=TutorMode.SOCRATIC)
    assert "session_id" in started
    turn = tutor_turn(lib, started["session_id"], "I think justice is fairness")
    assert turn["suggested_reply_to_learner"]
    rec = record_mastery(lib, started["session_id"], started["opening"]["concept_id"], 0.8)
    assert rec["mastery"]


def test_avicenna_tutor_session(tmp_path: Path):
    lib = Library(
        skills_dir=ROOT / "skills",
        library_dir=tmp_path / "library",
        sessions_dir=tmp_path / "sessions",
    )
    started = start_tutor(lib, "avicenna-canon", mode=TutorMode.AVICENNA)
    assert started["opening"]["mode"] == "avicenna"
    assert "canon_path" in started["opening"]
    turn = tutor_turn(lib, started["session_id"], "idk")
    reply = turn["suggested_reply_to_learner"].lower()
    assert "define" in reply or "definition" in reply
    assert "genus" in reply


def test_playbook_and_framework(tmp_path: Path):
    lib = Library(
        skills_dir=ROOT / "skills",
        library_dir=tmp_path / "library",
        sessions_dir=tmp_path / "sessions",
    )
    pb = start_playbook(lib, "socratic-method", "elenchus-loop")
    assert pb["step"]["id"] == "claim"
    pkg = lib.get("avicenna-canon")
    assert pkg
    fw = apply_framework(pkg, "hadd-burhan", "Is simplicity a virtue in API design?")
    assert "definition" in [f["name"] for f in fw["fields"]]


def test_import_markdown(tmp_path: Path):
    lib = Library(
        skills_dir=tmp_path / "skills",
        library_dir=tmp_path / "library",
        sessions_dir=tmp_path / "sessions",
        extra_skill_dirs=[],
    )
    sample = ROOT / "examples" / "sample_book.md"
    pkg = import_file(
        lib,
        sample,
        title="Talking to Users",
        license_kind=LicenseKind.USER_OWNED,
        ownership_attested=True,
        domains=["product", "research"],
        book_id="talking-to-users",
        sandbox_roots=[ROOT / "examples"],
    )
    assert pkg.card.id == "talking-to-users"
    assert pkg.excerpts
    assert pkg.curriculum
    assert lib.get("talking-to-users") is not None


def test_build_skill_from_text_levels():
    text = "# One\n\nHello world method steps here.\n\n# Two\n\nMore content about practice and judgment."
    pkg = build_skill_from_text(text=text, title="Tiny", license_kind=LicenseKind.PUBLIC_DOMAIN)
    assert pkg.playbooks and pkg.frameworks and pkg.rubrics and pkg.curriculum
    assert pkg.effective_level().value == "L4"
