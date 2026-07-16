"""Socratic and Avicenna-mode tutoring sessions (L4 mentor)."""

from __future__ import annotations

from typing import Any

from book_skills_mcp.models import (
    CurriculumConcept,
    SkillPackage,
    TutorMode,
    TutorSession,
)
from book_skills_mcp.search import search_library
from book_skills_mcp.store import Library


def _concept_map(pkg: SkillPackage) -> dict[str, CurriculumConcept]:
    if not pkg.curriculum:
        return {}
    return {c.id: c for c in pkg.curriculum.concepts}


def _pick_concept(pkg: SkillPackage, concept_id: str | None, mastery: dict[str, float]) -> CurriculumConcept | None:
    concepts = pkg.curriculum.concepts if pkg.curriculum else []
    if not concepts:
        return None
    if concept_id:
        for c in concepts:
            if c.id == concept_id or c.name.lower() == concept_id.lower():
                return c
    # first concept with mastery < 0.7, else first
    for c in concepts:
        if mastery.get(c.id, 0.0) < 0.7:
            return c
    return concepts[0]


def _socratic_opening(concept: CurriculumConcept, book_title: str) -> dict[str, Any]:
    questions = concept.key_questions or [
        f"In your own words, what is '{concept.name}' about?",
        f"Where have you seen something like '{concept.name}' outside the book?",
    ]
    return {
        "mode": TutorMode.SOCRATIC.value,
        "concept_id": concept.id,
        "concept": concept.name,
        "tutor_move": "elencus_open",
        "message": (
            f"We will examine **{concept.name}** from *{book_title}* by questions, "
            f"not lectures. Claim something brief, then we will test it."
        ),
        "primary_question": questions[0],
        "followups": questions[1:3],
        "watch_for_misconceptions": concept.misconceptions,
        "agent_instructions": [
            "Do NOT dump a full lecture.",
            "Ask one main question at a time.",
            "When the learner answers, press for definition, example, and counter-example.",
            "Only after a clear definition, offer a short book-aligned correction with a citation.",
            "Never invent quotations; use skill_search / skill_cite.",
        ],
    }


def _avicenna_opening(concept: CurriculumConcept, book_title: str) -> dict[str, Any]:
    """Avicenna (Ibn Sina) pedagogical style: definition → division → demonstration → application."""
    return {
        "mode": TutorMode.AVICENNA.value,
        "concept_id": concept.id,
        "concept": concept.name,
        "tutor_move": "definition_first",
        "canon_path": [
            "1. Definition (hadd) — what is it, genus + differentia",
            "2. Division (qisma) — parts, species, or aspects",
            "3. Demonstration (burhan) — reasons / causes, not mere authority",
            "4. Application — particular case under the universal",
            "5. Objection & reply — steelman a doubt, then answer",
        ],
        "message": (
            f"Avicenna-mode for **{concept.name}** (*{book_title}*): "
            f"we begin with a precise definition, then divide, then prove, then apply. "
            f"Vague slogans are not knowledge."
        ),
        "primary_question": (
            f"Give a one-sentence definition of '{concept.name}' "
            f"(what kind of thing it is, and what sets it apart)."
        ),
        "followups": [
            f"Divide '{concept.name}' into its main parts or kinds.",
            f"What cause or reason makes '{concept.name}' true or useful?",
            f"Apply '{concept.name}' to one concrete case from your life or work.",
        ],
        "agent_instructions": [
            "Prefer ordered, syllogistic clarity over rhetorical flourish.",
            "If the learner is vague, demand genus + differentia.",
            "After a good definition, move to division; do not skip steps.",
            "Cite the skill package when claiming the book teaches X.",
            "Distinguish historical Avicennan science from modern consensus when relevant.",
            "This is educational philosophy/history of ideas — not medical advice.",
        ],
        "safety": [
            "Not a substitute for licensed medical, legal, or mental-health care.",
            "Historical medicine in classical texts may be false or unsafe today.",
        ],
    }


def _explain_pack(pkg: SkillPackage, concept: CurriculumConcept) -> dict[str, Any]:
    hits = search_library([pkg], concept.name, book_id=pkg.card.id, limit=3)
    return {
        "mode": TutorMode.EXPLAIN.value,
        "concept_id": concept.id,
        "concept": concept.name,
        "summary": concept.summary,
        "key_questions": concept.key_questions,
        "misconceptions": concept.misconceptions,
        "supporting_excerpts": [h.model_dump() for h in hits],
        "agent_instructions": [
            "Explain in plain language, then map to book language.",
            "Include at least one citation from supporting_excerpts.",
            "End with one check question.",
        ],
    }


def _quiz_pack(concept: CurriculumConcept) -> dict[str, Any]:
    qs = concept.key_questions or [f"Explain {concept.name}."]
    return {
        "mode": TutorMode.QUIZ.value,
        "concept_id": concept.id,
        "concept": concept.name,
        "items": [
            {"id": f"q{i+1}", "prompt": q, "type": "short_answer"}
            for i, q in enumerate(qs[:5])
        ],
        "grading_hint": (
            "Score each answer 0–1 for clarity, fidelity to the concept, and an example. "
            "Update mastery via tutor_record_mastery."
        ),
    }


def start_tutor(
    library: Library,
    book_id: str,
    mode: TutorMode | str = TutorMode.SOCRATIC,
    concept_id: str | None = None,
) -> dict[str, Any]:
    pkg = library.get(book_id)
    if not pkg:
        raise ValueError(f"Unknown book_id '{book_id}'. Use library_list.")
    mode_e = TutorMode(mode) if not isinstance(mode, TutorMode) else mode
    if not pkg.curriculum or not pkg.curriculum.concepts:
        raise ValueError(
            f"Book '{book_id}' has no curriculum. Rebuild at L4 or use a demo skill "
            f"(avicenna-canon, socratic-method)."
        )
    concept = _pick_concept(pkg, concept_id, {})
    if not concept:
        raise ValueError("No concepts available.")
    session = TutorSession(
        session_id=library.new_id("tutor"),
        book_id=book_id,
        mode=mode_e,
        concept_id=concept.id,
        open_questions=list(concept.key_questions[:3]),
    )
    library.save_tutor_session(session)

    if mode_e == TutorMode.SOCRATIC:
        opening = _socratic_opening(concept, pkg.card.title)
    elif mode_e == TutorMode.AVICENNA:
        opening = _avicenna_opening(concept, pkg.card.title)
    elif mode_e == TutorMode.EXPLAIN:
        opening = _explain_pack(pkg, concept)
    elif mode_e == TutorMode.QUIZ:
        opening = _quiz_pack(concept)
    elif mode_e == TutorMode.COACH:
        opening = {
            "mode": mode_e.value,
            "concept_id": concept.id,
            "message": f"Coach mode on {concept.name}: set a goal, apply one playbook step, review.",
            "primary_question": f"What outcome do you want using '{concept.name}' this week?",
            "agent_instructions": [
                "Keep commitments small and checkable.",
                "Link to a playbook step when one exists.",
            ],
        }
    else:
        # exhaustive for future enum members
        opening = _socratic_opening(concept, pkg.card.title)

    return {
        "session_id": session.session_id,
        "book_id": book_id,
        "book_title": pkg.card.title,
        "level": pkg.card.level.value,
        "opening": opening,
    }


def tutor_turn(
    library: Library,
    session_id: str,
    learner_message: str,
) -> dict[str, Any]:
    session = library.load_tutor_session(session_id)
    if not session:
        raise ValueError(f"Unknown tutor session '{session_id}'.")
    if session.status != "active":
        raise ValueError(f"Session is {session.status}.")
    pkg = library.get(session.book_id)
    if not pkg:
        raise ValueError("Book for session no longer loaded.")
    concept = _pick_concept(pkg, session.concept_id, session.mastery)
    session.turns.append({"role": "learner", "text": learner_message.strip()[:4000]})
    library.save_tutor_session(session)

    claim = learner_message.strip()
    text = claim.lower()
    length = len(claim)
    vague = length < 40 or text in {"idk", "i don't know", "dunno", "maybe", "yes", "no"}
    # Surface the claim so elenchus targets the sentence, not only the curriculum label
    claim_bit = claim if length <= 180 else claim[:177] + "…"
    concept_label = concept.name if concept else "this idea"

    if session.mode == TutorMode.AVICENNA:
        if vague:
            move = "demand_definition"
            prompt = (
                f"That is still too thin for Avicenna-mode. You said: “{claim_bit}”. "
                f"Define the load-bearing term (or **{concept_label}**) with genus "
                f"(what kind of thing) and differentia (what sets it apart). One sentence that could be false."
            )
        elif any(w in text for w in ("because", "cause", "reason", "therefore", "since")):
            move = "press_application"
            prompt = (
                f"Good — you offered a reason about “{claim_bit}”. Now apply the universal to a particular: "
                "one concrete case, and state which clause of your definition covers it."
            )
        elif any(w in text for w in ("is a", "is an", "means", "defined as", "kind of")):
            move = "test_definition_then_divide"
            prompt = (
                f"Working definition noted: “{claim_bit}”. "
                f"Would this still hold if we changed the differentia? "
                f"Then divide **{concept_label}** (or your subject) into 2–4 parts/kinds relevant to your goal."
            )
        else:
            move = "ask_division_or_proof"
            prompt = (
                f"Acceptable start on “{claim_bit}”. Next: either (a) divide **{concept_label}** "
                f"into parts/kinds, or (b) give a short demonstration (why it must be so). Choose one."
            )
        instructions = [
            "Stay in definition → division → demonstration → application order.",
            "Target the learner's sentence; do not ignore their claim to lecture the chapter title.",
            "If the learner confuses modern science with classical claims, flag the difference.",
            "Cite excerpts when stating what the book teaches.",
            "Slogans without genus+differentia are not knowledge (press for a falsifiable differentia).",
        ]
    elif session.mode == TutorMode.SOCRATIC:
        if vague:
            move = "clarify"
            prompt = (
                f"What do you mean by “{claim_bit}”, exactly? "
                "Give a definition or a concrete example — one defendable sentence."
            )
        elif "?" in learner_message:
            move = "reflect_question"
            prompt = (
                "Interesting question. Before I answer: what would have to be true for your "
                "question to make sense? State your assumption as a claim."
            )
        else:
            move = "elenchus"
            prompt = (
                f"You claimed: “{claim_bit}”. Suppose the opposite. What breaks? "
                f"Then repair the claim so it still speaks to **{concept_label}** without humiliation of persons — "
                "only of weak sentences."
            )
        instructions = [
            "Prefer questions over answers until the learner has a clear claim.",
            "Quote or paraphrase their claim in the next move (claim focus).",
            "Expose contradiction gently; do not humiliate.",
            "When settled, give a short synthesis with a citation.",
            "If they want a direct answer or are in distress, switch mode (dialogue ethics).",
        ]
    else:
        move = "continue"
        prompt = (
            f"Continue from “{claim_bit}”; keep teaching moves short and check understanding of **{concept_label}**."
        )
        instructions = ["Stay on concept", "Cite when claiming book content"]

    hits = []
    if concept:
        hits = [h.model_dump() for h in search_library([pkg], concept.name, book_id=pkg.card.id, limit=2)]

    reply = {
        "session_id": session.session_id,
        "mode": session.mode.value,
        "concept_id": session.concept_id,
        "tutor_move": move,
        "suggested_reply_to_learner": prompt,
        "agent_instructions": instructions,
        "related_excerpts": hits,
        "mastery": session.mastery,
        "open_questions": session.open_questions,
    }
    session.turns.append({"role": "tutor_hint", "text": prompt})
    library.save_tutor_session(session)
    return reply


def record_mastery(
    library: Library,
    session_id: str,
    concept_id: str,
    score: float,
    note: str = "",
) -> dict[str, Any]:
    session = library.load_tutor_session(session_id)
    if not session:
        raise ValueError(f"Unknown tutor session '{session_id}'.")
    score = max(0.0, min(1.0, float(score)))
    session.mastery[concept_id] = score
    if note:
        session.turns.append({"role": "system", "text": f"mastery {concept_id}={score}: {note[:500]}"})
    # advance concept if mastered
    pkg = library.get(session.book_id)
    if pkg and pkg.curriculum and score >= 0.7:
        ids = [c.id for c in pkg.curriculum.concepts]
        if concept_id in ids:
            idx = ids.index(concept_id)
            if idx + 1 < len(ids):
                session.concept_id = ids[idx + 1]
    library.save_tutor_session(session)
    return {
        "session_id": session.session_id,
        "mastery": session.mastery,
        "current_concept_id": session.concept_id,
        "status": session.status,
    }


def grade_with_rubric(
    pkg: SkillPackage,
    rubric_id: str,
    work_summary: str,
    scores: dict[str, float] | None = None,
) -> dict[str, Any]:
    rubric = next((r for r in pkg.rubrics if r.id == rubric_id or r.name.lower() == rubric_id.lower()), None)
    if not rubric:
        raise ValueError(f"Rubric '{rubric_id}' not found. Available: {[r.id for r in pkg.rubrics]}")
    scores = scores or {}
    details = []
    weighted = 0.0
    total_w = 0.0
    for c in rubric.criteria:
        s = scores.get(c.id)
        if s is None:
            # heuristic: keyword presence
            s = 0.55 if c.name.lower().split()[0] in work_summary.lower() else 0.4
        s = max(0.0, min(1.0, float(s)))
        weighted += s * c.weight
        total_w += c.weight
        details.append(
            {
                "criterion_id": c.id,
                "name": c.name,
                "score": s,
                "weight": c.weight,
                "description": c.description,
            }
        )
    overall = weighted / total_w if total_w else 0.0
    return {
        "rubric_id": rubric.id,
        "rubric_name": rubric.name,
        "overall": round(overall, 3),
        "passed": overall >= rubric.pass_threshold,
        "threshold": rubric.pass_threshold,
        "criteria": details,
        "note": "Provide explicit criterion scores for fair grading; heuristics are a fallback only.",
    }
