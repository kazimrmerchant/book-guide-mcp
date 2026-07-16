"""Full Avicenna + Socratic challenge suite against Book Guide MCP product claims."""

from __future__ import annotations

from pathlib import Path

from book_skills_mcp.builder import build_skill_from_text, classify_genre
from book_skills_mcp.models import LicenseKind, TextGenre, TutorMode
from book_skills_mcp.playbooks import apply_framework, start_playbook, advance_playbook
from book_skills_mcp.search import match_skills, search_library
from book_skills_mcp.store import Library
from book_skills_mcp.tutor import grade_with_rubric, start_tutor, transfer_test, tutor_turn

ROOT = Path(__file__).resolve().parents[1]

PRODUCT_CLAIM = (
    "Book Guide MCP turns books you own into agent skill packages: "
    "citations, playbooks, frameworks, and Socratic/Avicenna tutors — "
    "local-first, not a raw RAG dump, not medical advice."
)

PRODUCT_DEFINITION = (
    "A local MCP skill package is executable method (card, playbooks, frameworks, curriculum) "
    "plus citable excerpts — genus: MCP server tool surface; differentia: ordered methods and "
    "sessions rather than retrieval-only chat."
)


def _lib(tmp_path: Path | None = None) -> Library:
    if tmp_path is None:
        return Library(skills_dir=ROOT / "skills", library_dir=ROOT / "library")
    return Library(
        skills_dir=ROOT / "skills",
        library_dir=tmp_path / "library",
        sessions_dir=tmp_path / "sessions",
    )


def test_genre_narrative_vs_method():
    novel = (
        "Once upon a time the king whispered to the dragon. "
        "She said nothing. He said he loved the kingdom. Suddenly the detective arrived. "
        "Chapter 1 of the novel continued with murder and a love story."
    )
    handbook = (
        "# Onboarding\n\n"
        "First, define the problem. Second, apply the checklist. "
        "You should use this method: step 1 procedure, step 2 verify, step 3 write the guideline. "
        "Do not skip the exercise. Framework and principle below."
    )
    g1, notes1, _ = classify_genre(novel, "Dragon Kingdom")
    g2, notes2, score2 = classify_genre(handbook, "Team Handbook")
    assert g1 == TextGenre.NARRATIVE
    assert g2 == TextGenre.METHOD
    assert score2 > 0.3
    assert any("narrative" in n.lower() or "method" in n.lower() for n in notes1 + notes2)

    n_pkg = build_skill_from_text(
        text=novel * 3,
        title="Dragon Tale",
        license_kind=LicenseKind.PUBLIC_DOMAIN,
        book_id="dragon-tale",
    )
    assert n_pkg.genre == TextGenre.NARRATIVE
    assert n_pkg.playbooks == []
    assert n_pkg.effective_level().value in {"L0", "L1"}
    assert n_pkg.card.level.value in {"L0", "L1"}

    m_pkg = build_skill_from_text(
        text=handbook * 2,
        title="Ops Handbook",
        license_kind=LicenseKind.USER_OWNED,
        book_id="ops-handbook",
    )
    assert m_pkg.genre == TextGenre.METHOD
    assert m_pkg.playbooks
    assert any(s.id == "transfer" for s in m_pkg.playbooks[0].steps)
    assert m_pkg.effective_level().value == "L4"


def test_avicenna_full_challenge(tmp_path: Path):
    lib = _lib(tmp_path)
    avi = lib.get("avicenna-canon")
    assert avi and avi.genre == TextGenre.METHOD

    # 1) Definition + division via framework seed
    fw = apply_framework(avi, "hadd-burhan", PRODUCT_CLAIM)
    subject = next(f for f in fw["fields"] if f["name"] == "subject")
    assert subject["value"] and "Book Guide" in subject["value"]
    assert "definition" in fw["missing_required"]

    # 2) Fill as host would after reading product definition
    filled = apply_framework(
        avi,
        "hadd-burhan",
        PRODUCT_CLAIM,
        {
            "subject": PRODUCT_CLAIM,
            "definition": PRODUCT_DEFINITION,
            "division": (
                "A Library cite; B Guide card; C Playbook; D Framework; "
                "E Mentor tutors; F Sandboxed import"
            ),
            "demonstration": (
                "Agents need progressive skill load and citations to avoid invented quotes; "
                "sessions enable ordered pedagogy; sandbox enforces ownership."
            ),
            "particular": (
                "User imports sample_book.md, runs guided-study, cites ex_0001 on a live task."
            ),
            "objection_reply": (
                "Objection: just RAG. Reply: retrieval is part A only; C–E are the differentia."
            ),
            "citations": "ex_0001,ex_0002,ex_0003",
        },
    )
    assert filled["missing_required"] == []

    # 3) Evidence search
    hits = search_library([avi], "slogan definition method knowledge", limit=3)
    assert hits and hits[0].book_id == "avicenna-canon"

    # 4) Tutor with claim about the product
    started = start_tutor(lib, "avicenna-canon", mode=TutorMode.AVICENNA, concept_id="concept_002")
    turn = tutor_turn(
        lib,
        started["session_id"],
        "A book skill is a package of executable method plus citable excerpts",
    )
    assert "package" in turn["suggested_reply_to_learner"].lower() or "executable" in turn[
        "suggested_reply_to_learner"
    ].lower()

    # 5) Transfer test worksheet
    tt = transfer_test(
        avi,
        "concept_002",
        "Import a handbook and run guided-study",
        "Use Socratic tutor on a PR design review instead",
    )
    assert tt["trained_case"] and tt["fresh_case"]
    assert tt["fresh_case"] != tt["trained_case"]
    assert "imitation" in " ".join(tt["agent_instructions"]).lower()

    # 6) Rubric — strong definition/division should pass
    grade = grade_with_rubric(
        avi,
        "avicenna-fidelity",
        PRODUCT_DEFINITION + " division playbook framework tutor cite",
        {
            "definition_quality": 0.9,
            "division_clarity": 0.85,
            "demonstration": 0.85,
            "application": 0.8,
            "safety_humility": 1.0,
        },
    )
    assert grade["passed"] is True
    assert grade["overall"] >= 0.7


def test_socratic_full_challenge(tmp_path: Path):
    lib = _lib(tmp_path)
    soc = lib.get("socratic-method")
    assert soc and soc.genre == TextGenre.METHOD

    # Ethics gate seeds
    ethics = apply_framework(
        soc,
        "dialogue-ethics",
        "User is calm and asked for Socratic teaching on product claims",
        {
            "user_state": "calm",
            "need_type": "exploration",
            "consent": "wants questions",
            "decision": "socratic",
            "rationale": "Safe educational critique of product definition",
        },
    )
    assert ethics["missing_required"] == []

    # Elenchus worksheet
    elenchus = apply_framework(
        soc,
        "elenchus-worksheet",
        "Book Guide MCP is just RAG with extra steps",
        {
            "claim": "Book Guide MCP is just RAG with extra steps",
            "key_terms": "RAG = retrieval; skill package = method+cite+sessions",
            "example": "skill_search alone would be RAG-like",
            "counterexample": "tutor_start + playbook_next require session method, not retrieval only",
            "tension": "If only RAG, removing tutors would not change outcomes — but it does",
            "revised_claim": (
                "Retrieval is necessary (L0) but not sufficient; differentia is ordered method "
                "and mentor sessions (L2–L4)"
            ),
            "open_question": "How much auto-playbook quality varies by genre?",
        },
    )
    assert elenchus["missing_required"] == []
    claim_field = next(f for f in elenchus["fields"] if f["name"] == "claim")
    assert "RAG" in (claim_field["value"] or "")

    # Tutor elenchus quotes claim
    started = start_tutor(lib, "socratic-method", mode=TutorMode.SOCRATIC)
    claim = "Book Guide MCP is just RAG with extra steps"
    turn = tutor_turn(lib, started["session_id"], claim)
    assert "RAG" in turn["suggested_reply_to_learner"]
    assert turn["tutor_move"] == "elenchus"

    # Playbook full path at least starts and advances
    pb = start_playbook(lib, "socratic-method", "elenchus-loop")
    assert pb["step"]["id"] == "claim"
    nxt = advance_playbook(lib, pb["session_id"], answer=claim)
    assert nxt["status"] in {"active", "completed"}

    # Rubric for good Socratic product critique
    grade = grade_with_rubric(
        soc,
        "socratic-quality",
        "One question at a time; claim focus on RAG slogan; no humiliation; dignity first",
        {
            "one_question": 0.9,
            "claim_focus": 0.9,
            "definition_work": 0.85,
            "non_humiliation": 1.0,
            "boundary": 0.9,
        },
    )
    assert grade["passed"] is True


def test_match_prefers_method_demos_for_method_tasks():
    lib = _lib()
    ranked = match_skills(
        lib.list_packages(),
        "socratic elenchus and avicenna definition tutor for agent skills",
        limit=5,
    )
    ids = [m.book_id for m in ranked]
    assert ids[0] in {"socratic-method", "avicenna-canon"}
    assert "socratic-method" in ids and "avicenna-canon" in ids


def test_transfer_and_server_tool_surface():
    from book_skills_mcp.server import mcp

    names = list(mcp._tool_manager._tools.keys())  # noqa: SLF001 — test surface
    assert "skill_transfer_test" in names
    lib = _lib()
    pkg = lib.get("socratic-method")
    assert pkg
    out = transfer_test(pkg, None, "case A: import handbook", "case B: review PR design")
    assert "case B" in out["fresh_case"]
