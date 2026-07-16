# Ship under fire — Avicenna + Socratic challenge of Book Guide MCP

We turned the **demo books on the product itself**. Below: **definition**, **division**, **elenchus**, bugs found, and **ship improvements** that landed in **v0.2.0**.

---

## 1. Definition (Avicenna: genus + differentia)

| | |
|--|--|
| **Genus** | A **local Model Context Protocol (MCP) server** for AI agents |
| **Differentia** | Turns books the user owns (or public-domain texts) into **executable skill packages** — routing cards, citable excerpts, multi-step playbooks, frameworks, and mentor tutors — **not** a raw full-text dump, **not** a fine-tuned model, **not** clinical advice |

**Slogan we rejected:** “AI for books” (empty universal).  
**Test of differentia:** if we only retrieved chunks without playbooks/frameworks/tutor order, it would fail the definition.

---

## 2. Division (so disputes do not talk past each other)

| Part | What Book Guide MCP is | What it is not |
|------|------------------------|----------------|
| **A. Library** | Search + cite with locators | Piracy / full-book redistribution |
| **B. Guide card** | When-to-use routing | Generic system prompt fluff |
| **C. Playbook** | Multi-step procedures | One-shot chat completion |
| **D. Framework** | Structured worksheets (hadd-burhan, elenchus) | Unstructured “think hard” |
| **E. Mentor** | Socratic / Avicenna session state | Therapy or medical care |
| **F. Import** | Sandboxed build of L4 packages | Arbitrary filesystem access |

Many “is this just RAG?” fights are **part A vs C–E** confusion.

---

## 3. Socratic elenchus (claim focus)

**Claim under test:** *“Book Guide MCP is just RAG with extra steps.”*

| Move | Result |
|------|--------|
| Assume the opposite | If it were *only* RAG, removing playbooks/tutors would not change agent behavior — but demos require `tutor_start` / `skill_framework_apply` |
| Repair | Fair claim: *retrieval (A) is necessary but not sufficient; the product’s differentia is ordered method + sessions (C–E)* |

**Product bug found:** tutor turns often ignored the learner’s sentence and only pressed the curriculum title. **Fixed:** replies now quote the learner claim.

---

## 4. Demonstration (why the architecture must be so)

1. Agents load **skills** cheaply (card first) — progressive disclosure.  
2. Citations require **locators**, not vibes — anti-hallucination.  
3. Teaching requires **session state** — multi-turn elenchus / hadd order.  
4. Ownership + sandbox — legal and security constraints, not optional polish.

---

## 5. Particular case (this challenge run)

| Check | Before | After |
|-------|--------|-------|
| `skill_framework_apply(context=…)` | `subject` stayed empty (bug: only seeded field named `context`) | Seeds `subject` / `claim` / etc. |
| `skill_match("socratic…")` | Weak ranking vs unrelated sample skills | Intent boosts + curriculum/excerpt text |
| Socratic `tutor_turn` | “Repair claim about Inquiry over performance” without quoting user | Quotes user claim, then elenchus |
| Server instructions | Feature list only | Includes genus+differentia definition |

---

## 6. Objection & reply

| Objection | Reply |
|-----------|--------|
| Auto-import L4 from any PDF is weak method | True for novels; we still scaffold study playbooks — genre detection remains a roadmap item |
| Host model still does the talking | By design: tools supply **moves and evidence**, not a second LLM bill |
| Avicenna package could be misread as medicine | Safety excerpts + when_not_to_use + server instructions |

---

## 7. Rubric (honest self-score)

| When | Result |
|------|--------|
| Marketing slogan only | Failed ~0.54 (weak definition/division) |
| Full definition + division + particular + safety | **Pass** ≥0.7 (see automated suite) |

**Lesson:** ship the definition in agent instructions and examples, not only in README slogans.

---

## 8. All roadmap items (this pass)

| Item | Status |
|------|--------|
| Genre detection (novels ≠ L4 playbooks) | `classify_genre` + narrative → L0/L1 |
| Transfer test (fresh particular) | `skill_transfer_test` tool + playbook **transfer** step |
| Host model supplies prose | Documented in server instructions + safety notes |
| Re-run Avicenna + Socratic suite | `tests/test_challenge_books.py` |

---

## Try the same challenge

```text
skill_framework_apply(
  book_id="avicenna-canon",
  framework_id="hadd-burhan",
  context="Book Guide MCP turns books into agent skills"
)
# Expect: subject seeded; definition/division/demonstration still missing → agent must fill

tutor_start(book_id="socratic-method", mode="socratic")
tutor_turn(session_id=…, learner_message="This is just RAG with extra steps")
# Expect: reply quotes that claim

skill_transfer_test(
  book_id="avicenna-canon",
  trained_case="Import a handbook and run guided-study",
  fresh_case="Use Socratic tutor on a PR design review"
)
```

Automated: `pytest tests/test_challenge_books.py -q`
