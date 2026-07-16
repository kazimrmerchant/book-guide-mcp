# Ship cleaner decisions — Avicenna method lens on real work

**Outcome:** Analyze a live decision with ordered method (**definition → division → demonstration → application**).

**Demo skill:** `avicenna-canon`  
**Safety:** Educational method only — **not medical advice**.

---

## Infographic

![Avicenna framework flow](../assets/example-avicenna-flow.svg)

---

## You say

> Review this API design claim with Avicenna method:  
> “Our public API should be as simple as possible.”

## What the agent does (tools)

### 1. Match / open (optional)

```text
skill_match(task="methodical definition and proof for a design claim")
skill_open(book_id="avicenna-canon")
```

### 2. Apply framework

```text
skill_framework_apply(
  book_id="avicenna-canon",
  framework_id="hadd-burhan",
  context="Public API should be as simple as possible"
)
```

### 3. Sample tool result (shape)

```json
{
  "framework_id": "hadd-burhan",
  "framework_name": "Hadd → Burhan lens",
  "fields": [
    { "name": "subject", "value": "Public API should be as simple as possible", "required": true },
    { "name": "definition", "value": null, "required": true },
    { "name": "division", "value": null, "required": true },
    { "name": "demonstration", "value": null, "required": true },
    { "name": "particular", "value": null, "required": true }
  ],
  "missing_required": ["definition", "division", "demonstration", "particular"],
  "agent_instructions": [
    "Fill missing_required fields using skill_search for evidence.",
    "Do not invent quotations; use skill_cite for any quote."
  ]
}
```

### 4. Evidence

```text
skill_search(query="definition genus differentia", book_id="avicenna-canon")
skill_cite(book_id="avicenna-canon", excerpt_id="ex_0002")
```

### 5. What you see from the agent (filled worksheet)

```text
Subject: “Public API should be as simple as possible”

1) Definition (hadd)
   Genus: a design principle for public interfaces.
   Differentia: prefers fewer concepts and stable defaults over maximum power.

2) Division (qisma)
   - Surface simplicity (names, count of endpoints)
   - Cognitive simplicity (mental model)
   - Operational simplicity (ops, versioning)
   - Expressiveness trade-offs

3) Demonstration (burhan)
   Middle term: fewer degrees of freedom → fewer misuse modes.
   Falsifier: a “simple” API that forces N workarounds is not simple in use.

4) Particular
   Case: pagination. One cursor style everywhere beats three styles “for flexibility.”

Citation: "What a definition must do" — Avicenna Canon skill, method/2§1
```

### 6. Optional grade

```text
skill_grade(
  book_id="avicenna-canon",
  rubric_id="avicenna-fidelity",
  work_summary="<paste the worksheet>",
  scores_json="{\"definition_quality\":0.85,\"demonstration\":0.8,\"application\":0.75,\"safety_humility\":1.0}"
)
```

---

## What to expect (checklist)

| Expect | Do **not** expect |
|--------|-------------------|
| Ordered steps (define before argue) | Vague “keep it simple” slogans only |
| Explicit missing fields to fill | Silent completion without evidence |
| Safety framing for historical medicine topics | Clinical prescriptions from the Canon skill |
| Rubric scores when you ask to grade | Perfect scores without criterion scores |

---

## Try it

```text
skill_framework_apply(
  book_id="avicenna-canon",
  framework_id="hadd-burhan",
  context="Your claim or design here"
)
```
