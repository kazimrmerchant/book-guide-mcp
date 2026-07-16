"""Playbook and framework runners (L2–L3)."""

from __future__ import annotations

from typing import Any

from book_skills_mcp.models import Framework, Playbook, PlaybookSession, SkillPackage
from book_skills_mcp.store import Library


def get_playbook(pkg: SkillPackage, playbook_id: str) -> Playbook:
    for p in pkg.playbooks:
        if p.id == playbook_id or p.name.lower() == playbook_id.lower():
            return p
    raise ValueError(
        f"Playbook '{playbook_id}' not found. Available: {[p.id for p in pkg.playbooks]}"
    )


def get_framework(pkg: SkillPackage, framework_id: str) -> Framework:
    for f in pkg.frameworks:
        if f.id == framework_id or f.name.lower() == framework_id.lower():
            return f
    raise ValueError(
        f"Framework '{framework_id}' not found. Available: {[f.id for f in pkg.frameworks]}"
    )


def start_playbook(library: Library, book_id: str, playbook_id: str) -> dict[str, Any]:
    pkg = library.get(book_id)
    if not pkg:
        raise ValueError(f"Unknown book_id '{book_id}'.")
    pb = get_playbook(pkg, playbook_id)
    if not pb.steps:
        raise ValueError("Playbook has no steps.")
    session = PlaybookSession(
        session_id=library.new_id("pb"),
        book_id=book_id,
        playbook_id=pb.id,
        step_index=0,
    )
    library.save_playbook_session(session)
    step = pb.steps[0]
    return {
        "session_id": session.session_id,
        "book_id": book_id,
        "playbook_id": pb.id,
        "playbook_name": pb.name,
        "step_index": 0,
        "total_steps": len(pb.steps),
        "step": step.model_dump(),
        "status": "active",
    }


def advance_playbook(
    library: Library,
    session_id: str,
    answer: str = "",
    mark_complete: bool = False,
) -> dict[str, Any]:
    session = library.load_playbook_session(session_id)
    if not session:
        raise ValueError(f"Unknown playbook session '{session_id}'.")
    pkg = library.get(session.book_id)
    if not pkg:
        raise ValueError("Book missing for session.")
    pb = get_playbook(pkg, session.playbook_id)
    if answer:
        session.answers[f"step_{session.step_index}"] = answer[:8000]
    if mark_complete or session.step_index >= len(pb.steps) - 1:
        if session.step_index >= len(pb.steps) - 1 or mark_complete:
            if session.step_index >= len(pb.steps) - 1:
                session.status = "completed"
                library.save_playbook_session(session)
                return {
                    "session_id": session.session_id,
                    "status": "completed",
                    "answers": session.answers,
                    "message": "Playbook complete. Summarize outcomes and cite any excerpts used.",
                }
    session.step_index += 1
    if session.step_index >= len(pb.steps):
        session.status = "completed"
        library.save_playbook_session(session)
        return {
            "session_id": session.session_id,
            "status": "completed",
            "answers": session.answers,
        }
    library.save_playbook_session(session)
    step = pb.steps[session.step_index]
    return {
        "session_id": session.session_id,
        "status": "active",
        "step_index": session.step_index,
        "total_steps": len(pb.steps),
        "step": step.model_dump(),
        "answers_so_far": list(session.answers.keys()),
    }


# context= seeds these field names when the caller did not pass field_values
_CONTEXT_SEED_FIELDS = frozenset(
    {
        "context",
        "subject",
        "claim",
        "learner_definition",
        "work_summary",
        "situation",
    }
)


def apply_framework(
    pkg: SkillPackage,
    framework_id: str,
    context: str,
    field_values: dict[str, str] | None = None,
) -> dict[str, Any]:
    fw = get_framework(pkg, framework_id)
    field_values = field_values or {}
    ctx = context.strip()
    filled = []
    missing = []
    for field in fw.fields:
        val = field_values.get(field.name, "").strip()
        if not val and field.name in _CONTEXT_SEED_FIELDS and ctx:
            val = ctx
        if not val and field.required:
            missing.append(field.name)
        filled.append(
            {
                "name": field.name,
                "description": field.description,
                "value": val or None,
                "required": field.required,
                "example": field.example,
            }
        )
    seed_note = (
        f"Seeded from context into: "
        + ", ".join(
            f["name"]
            for f in filled
            if f["value"] == ctx and f["name"] in _CONTEXT_SEED_FIELDS
        )
        if ctx
        else ""
    )
    instructions = [
        "Fill missing_required fields using skill_search for evidence.",
        "Do not invent quotations; use skill_cite for any quote.",
        "Complete genus+differentia for any definition field (Avicenna: slogans are not knowledge).",
        f"Return a structured result matching: {fw.output_shape or 'framework fields'}",
    ]
    if seed_note:
        instructions.insert(0, seed_note + ". Refine that seed; do not leave it as a vague slogan.")
    return {
        "framework_id": fw.id,
        "framework_name": fw.name,
        "description": fw.description,
        "process": fw.process,
        "output_shape": fw.output_shape,
        "fields": filled,
        "missing_required": missing,
        "agent_instructions": instructions,
        "context": context,
    }
