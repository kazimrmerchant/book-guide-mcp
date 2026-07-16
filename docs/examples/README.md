# See it ship — what to expect when Book Guide MCP is connected

These are not abstract titles. Each walkthrough shows **tool sequences**, **sample JSON**, and **agent lines** you should actually get. No API keys. Demo skills ship in the repo.

**Ship improvements angle:** use these flows to improve *your* work (reviews, tutoring, imports) — not to generate more generic advice.

| Ship this outcome | You say… | Tools | Visual |
|-------------------|----------|-------|--------|
| [Socratic pressure that holds a claim](01-socratic-tutor.md) | “Quiz me on definitions” | `tutor_start` → `tutor_turn` | [flow](../assets/example-socratic-flow.svg) |
| [Methodical design review](02-avicenna-framework.md) | “Review this design methodically” | `skill_framework_apply` + cite | [flow](../assets/example-avicenna-flow.svg) |
| [Your handbook as a runnable skill](03-import-your-book.md) | “Turn my handbook into a skill” | `skill_import_file` → playbook | [flow](../assets/example-import-flow.svg) |
| [Product pressure-test with its own books](04-challenge-avicenna-socratic.md) | “Challenge this MCP with Avicenna + Socrates” | frameworks + tutor + transfer | — |

### Master overview — request → tools → guidance

![What to expect when using Book Guide MCP](../assets/what-to-expect-flow.svg)

<p align="center">
  <img src="../assets/what-to-expect-hero.png" alt="What to expect — books become agent guides" width="420"/>
</p>

### First 60 seconds (any host)

```text
You:  List my book skills.
Agent → library_list
Expect: avicenna-canon, socratic-method (and any you imported)

You:  Teach me with Socratic questions.
Agent → tutor_start(book_id="socratic-method", mode="socratic")
Expect: one primary question — not a lecture
```

Install & operate: [USAGE.md](../USAGE.md) · Release: **v0.2.0**
