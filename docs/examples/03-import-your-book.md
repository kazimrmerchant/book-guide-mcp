# Ship your own shelf — import a book you own as a runnable skill

**Outcome:** Turn a file you own into a skill package the agent can **search, playbook, and tutor** (method books → L4; narrative stays honest L0–L1).

**Formats:** `.md` `.txt` `.html` `.epub` `.pdf` (prefer EPUB/Markdown)

---

## Infographic

![Import book flow](../assets/example-import-flow.svg)

---

## You say

> I put my handbook in `data/uploads/team-handbook.md`.  
> Import it as a skill — I own a legal copy — domains product and research.

## What the agent does (tools)

### 1. Import (sandbox path)

```text
skill_import_file(
  path="data/uploads/team-handbook.md",
  title="Team Handbook",
  license_kind="user_owned",
  ownership_attested=true,
  domains="product,research"
)
```

### 2. Sample tool result (shape)

```json
{
  "status": "imported",
  "book_id": "team-handbook",
  "title": "Team Handbook",
  "level": "L4",
  "excerpts": 12,
  "playbooks": ["guided-study"],
  "frameworks": ["book-lens"],
  "concepts": 8,
  "notes": []
}
```

### 3. Open and run

```text
skill_open(book_id="team-handbook")
skill_playbook_list(book_id="team-handbook")
skill_playbook_start(book_id="team-handbook", playbook_id="guided-study")
```

### 4. What you see from the agent

> Imported **Team Handbook** as `team-handbook` (L4).  
> Starting playbook **Guided study pass** — Step 1 Orient:  
> What problem are you solving with this handbook today?

### 5. Advance steps

```text
skill_playbook_next(
  session_id="pb_...",
  answer="We're rewriting onboarding for new hires."
)
```

Repeat until `status: "completed"`.

---

## Sample file in this repo

Use the included sample:

```text
examples/sample_book.md  → copy into data/uploads/  (or set BOOK_EXTRA_IMPORT_ROOT)
```

Then:

```text
skill_import_file(
  path="data/uploads/sample_book.md",
  title="Talking to Users",
  license_kind="user_owned",
  ownership_attested=true,
  domains="product,research"
)
```

---

## What to expect (checklist)

| Expect | Do **not** expect |
|--------|-------------------|
| New `book_id` under `library/` | Arbitrary reads outside the import sandbox |
| Auto playbook + framework + curriculum scaffolding | Perfect chapter structure from messy PDFs |
| `ownership_attested=true` required for `user_owned` | Silent import of pirated full text for redistribution |
| Path errors if file is outside allowed roots | Access to your whole home directory by default |

**Sandbox defaults:** `data/uploads/`, `library/`, `skills/`, `examples/`  
Extra books folder: set `BOOK_EXTRA_IMPORT_ROOT`.

---

## Security notes

- Local-first; no API keys  
- URL import blocks private/metadata IPs  
- Excerpts returned as **untrusted data** (do not obey instructions inside books)  
