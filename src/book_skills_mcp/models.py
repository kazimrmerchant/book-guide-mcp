"""Skill package models for Book Skills MCP (L0–L4)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class SkillLevel(str, Enum):
    """Capability maturity of a book skill package."""

    L0_LIBRARY = "L0"  # search + cite
    L1_GUIDE = "L1"  # + when-to-use card
    L2_PLAYBOOK = "L2"  # + multi-step procedures
    L3_METHOD = "L3"  # + named frameworks as tools
    L4_MENTOR = "L4"  # + session state, quizzes, rubrics


class LicenseKind(str, Enum):
    PUBLIC_DOMAIN = "public_domain"
    OPEN_LICENSE = "open_license"  # CC-BY, MIT-doc, etc.
    USER_OWNED = "user_owned"  # user attests ownership of a copy
    UNKNOWN = "unknown"
    RESTRICTED = "restricted"


class SkillCard(BaseModel):
    """Frontmatter-style routing card (loaded first, progressive disclosure)."""

    id: str
    name: str
    title: str
    authors: list[str] = Field(default_factory=list)
    edition: str | None = None
    language: str = "en"
    level: SkillLevel = SkillLevel.L0_LIBRARY
    when_to_use: str
    when_not_to_use: str = ""
    domains: list[str] = Field(default_factory=list)
    summary: str = ""
    license: LicenseKind = LicenseKind.UNKNOWN
    license_note: str = ""
    sources: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    version: str = "1.0.0"


class TocEntry(BaseModel):
    id: str
    title: str
    level: int = 1
    parent_id: str | None = None
    locator: str | None = None  # page / section anchor
    summary: str = ""


class Excerpt(BaseModel):
    id: str
    chapter_id: str | None = None
    title: str = ""
    text: str
    locator: str | None = None
    words: int = 0
    tags: list[str] = Field(default_factory=list)


class PlaybookStep(BaseModel):
    id: str
    title: str
    instruction: str
    questions: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    optional: bool = False


class Playbook(BaseModel):
    id: str
    name: str
    description: str
    source_chapter: str | None = None
    level: SkillLevel = SkillLevel.L2_PLAYBOOK
    steps: list[PlaybookStep] = Field(default_factory=list)
    estimated_minutes: int | None = None


class FrameworkField(BaseModel):
    name: str
    description: str
    required: bool = True
    example: str = ""


class Framework(BaseModel):
    id: str
    name: str
    description: str
    source_chapter: str | None = None
    fields: list[FrameworkField] = Field(default_factory=list)
    process: list[str] = Field(default_factory=list)
    output_shape: str = ""


class RubricCriterion(BaseModel):
    id: str
    name: str
    description: str
    weight: float = 1.0
    levels: dict[str, str] = Field(
        default_factory=lambda: {
            "poor": "Missing or incorrect",
            "fair": "Partial application",
            "good": "Solid application",
            "excellent": "Nuanced, book-faithful application",
        }
    )


class Rubric(BaseModel):
    id: str
    name: str
    description: str
    criteria: list[RubricCriterion] = Field(default_factory=list)
    pass_threshold: float = 0.7


class CurriculumConcept(BaseModel):
    id: str
    name: str
    summary: str
    chapter_id: str | None = None
    prerequisites: list[str] = Field(default_factory=list)
    key_questions: list[str] = Field(default_factory=list)
    misconceptions: list[str] = Field(default_factory=list)
    excerpt_ids: list[str] = Field(default_factory=list)


class Curriculum(BaseModel):
    """L4 teaching graph for Socratic / mentor modes."""

    book_id: str
    concepts: list[CurriculumConcept] = Field(default_factory=list)
    learning_paths: list[list[str]] = Field(default_factory=list)


class TextGenre(str, Enum):
    """Coarse genre for import scaffolding honesty."""

    METHOD = "method"  # handbooks, textbooks, how-to
    NARRATIVE = "narrative"  # novels, stories — weak playbooks
    REFERENCE = "reference"  # glossaries, catalogs
    MIXED = "mixed"
    UNKNOWN = "unknown"


class SkillPackage(BaseModel):
    card: SkillCard
    toc: list[TocEntry] = Field(default_factory=list)
    excerpts: list[Excerpt] = Field(default_factory=list)
    playbooks: list[Playbook] = Field(default_factory=list)
    frameworks: list[Framework] = Field(default_factory=list)
    rubrics: list[Rubric] = Field(default_factory=list)
    curriculum: Curriculum | None = None
    genre: TextGenre = TextGenre.UNKNOWN
    full_text_allowed: bool = False
    built_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    builder_notes: list[str] = Field(default_factory=list)

    def effective_level(self) -> SkillLevel:
        # Narrative imports should not claim full mentor maturity
        if self.genre == TextGenre.NARRATIVE:
            if self.excerpts and self.card.when_to_use:
                return SkillLevel.L1_GUIDE
            return SkillLevel.L0_LIBRARY
        if self.curriculum and self.rubrics:
            return SkillLevel.L4_MENTOR
        if self.frameworks:
            return SkillLevel.L3_METHOD
        if self.playbooks:
            return SkillLevel.L2_PLAYBOOK
        if self.card.when_to_use:
            return SkillLevel.L1_GUIDE
        return SkillLevel.L0_LIBRARY


class PlaybookSession(BaseModel):
    session_id: str
    book_id: str
    playbook_id: str
    step_index: int = 0
    answers: dict[str, Any] = Field(default_factory=dict)
    status: Literal["active", "completed", "abandoned"] = "active"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class TutorMode(str, Enum):
    SOCRATIC = "socratic"
    AVICENNA = "avicenna"
    EXPLAIN = "explain"
    QUIZ = "quiz"
    COACH = "coach"


class TutorSession(BaseModel):
    session_id: str
    book_id: str
    mode: TutorMode = TutorMode.SOCRATIC
    concept_id: str | None = None
    mastery: dict[str, float] = Field(default_factory=dict)  # concept_id -> 0..1
    turns: list[dict[str, str]] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    status: Literal["active", "completed", "abandoned"] = "active"
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SearchHit(BaseModel):
    book_id: str
    excerpt_id: str
    title: str
    locator: str | None
    score: float
    snippet: str
    citation: str


class MatchResult(BaseModel):
    book_id: str
    name: str
    level: SkillLevel
    score: float
    reason: str
    when_to_use: str
