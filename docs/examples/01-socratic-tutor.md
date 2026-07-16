# Example 01 — Socratic tutor

**Goal:** Learn a concept by questions, not monologue.

**Demo skill:** `socratic-method`

---

## Infographic

![Socratic tutor flow](../assets/example-socratic-flow.svg)

---

## You say

> Quiz me on definitions using the Socratic skill. One question at a time.

## What the agent does (tools)

### 1. Start tutor

```text
tutor_start(
  book_id="socratic-method",
  mode="socratic"
)
```

### 2. Sample tool result (shape)

```json
{
  "session_id": "tutor_a1b2c3d4e5f6",
  "book_id": "socratic-method",
  "book_title": "Socratic Method — Elenchus as a Teaching Skill",
  "level": "L4",
  "opening": {
    "mode": "socratic",
    "concept_id": "concept_001",
    "concept": "Inquiry over performance",
    "primary_question": "When is a question more helpful than an answer?",
    "agent_instructions": [
      "Do NOT dump a full lecture.",
      "Ask one main question at a time."
    ]
  }
}
```

### 3. What you see from the agent

> **Primary question:** When is a question more helpful than an answer?  
> Take a short claim — one sentence is enough.

### 4. You answer

> When the other person already has the facts but is confused about meaning.

### 5. Continue

```text
tutor_turn(
  session_id="tutor_a1b2c3d4e5f6",
  learner_message="When the other person already has the facts but is confused about meaning."
)
```

### 6. Sample next move

```json
{
  "tutor_move": "elenchus",
  "suggested_reply_to_learner": "Suppose the opposite of what you just said. What breaks? Then repair your claim about Inquiry over performance.",
  "related_excerpts": [
    {
      "excerpt_id": "ex_0001",
      "snippet": "Socratic teaching is not a quiz show...",
      "citation": "\"Inquiry, not performance\" — Socratic Method..."
    }
  ]
}
```

### 7. What you see from the agent

> Suppose the opposite: they have the facts *and* the meaning is already clear.  
> When would a question still help?  
> (I’ll cite the skill after we lock a cleaner claim.)

### 8. Optional mastery

```text
tutor_record_mastery(
  session_id="tutor_a1b2c3d4e5f6",
  concept_id="concept_001",
  score=0.8,
  note="Clear when-to-question example"
)
```

---

## What to expect (checklist)

| Expect | Do **not** expect |
|--------|-------------------|
| One question at a time | A multi-page lecture |
| Pressure on your claim | Humiliation / “gotcha” bullying |
| Citations via `skill_cite` when quoting | Invented Plato quotes |
| Session id you can continue later | The full book dumped into chat |

---

## Try it

```text
library_list
tutor_start(book_id="socratic-method", mode="socratic")
```
