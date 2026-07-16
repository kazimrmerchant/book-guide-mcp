# Book Skills MCP

**Turn books into agent skills** — not another generic RAG chatbot.

Ship-ready [Model Context Protocol](https://modelcontextprotocol.io) server that converts books you own (or public-domain / open links) into **L0–L4 skill packages**: searchable library, playbooks, frameworks, rubrics, and mentor tutors — including **Socratic** and **Avicenna (Ibn Sina)** modes.

## Why

Agents already load *skills* (routing cards + procedures). Books are the densest source of trusted human expertise. This project treats a book as:

| Level | Name | Agent gets |
|-------|------|------------|
| **L0** | Library | Search + cite excerpts |
| **L1** | Guide | Skill card (`when_to_use`) |
| **L2** | Playbook | Multi-step procedures |
| **L3** | Method | Named frameworks as worksheets |
| **L4** | Mentor | Curriculum, quizzes, rubrics, tutor sessions |

**Methods first, full text second, citations always.**

## Demo skills (bundled)

| Skill id | What it is |
|----------|------------|
| `socratic-method` | Elenchus tutor: claim → definition → examples → test → synthesis |
| `avicenna-canon` | Avicenna-mode: definition → division → demonstration → application (**not medical advice**) |

## Quick start

```bash
cd book-skills-mcp
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -e ".[dev]"
book-skills-mcp
# or: python -m book_skills_mcp
```

### Cursor / Claude Desktop (`mcp.json`)

```json
{
  "mcpServers": {
    "book-skills": {
      "command": "python",
      "args": ["-m", "book_skills_mcp"],
      "cwd": "G:/My Drive/Cursor/Projects/book-skills-mcp",
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

Use your absolute path. On Windows, prefer the venv’s `python.exe` if the host PATH is thin:

```json
"command": "G:/My Drive/Cursor/Projects/book-skills-mcp/.venv/Scripts/python.exe"
```

### Environment (optional)

| Variable | Default | Meaning |
|----------|---------|---------|
| `BOOK_SKILLS_DIR` | package `bundled_skills/` | Skill packages to load |
| `BOOK_LIBRARY_DIR` | `./library` or user data dir | User-imported skills |
| `BOOK_SESSIONS_DIR` | `./sessions` or user data dir | Tutor / playbook sessions |
| `BOOK_UPLOADS_DIR` | `./data/uploads` or user data dir | Fetched URL cache |
| `BOOK_DATA_DIR` | OS app-data/`book-skills-mcp` | Root when not in a source checkout |
| `BOOK_IMPORT_ROOTS` | uploads + library + skills + examples | Sandbox for `skill_import_file` |
| `BOOK_EXTRA_IMPORT_ROOT` | unset | Extra allowed folder (e.g. `G:\Books`) |

See `.env.example`. **Never** set import roots to your entire home directory.

## Tools

### Library & evidence (L0–L1)

- `library_list` / `library_reload`
- `skill_match` — rank skills for a task
- `skill_open` — card + inventory
- `skill_search` / `skill_cite`
- `skill_status` / `skill_curriculum`

### Import

- `skill_import_file` — `.md` `.txt` `.html` `.epub` `.pdf`
- `skill_import_url` — http(s), size-capped; no paywall bypass

For `user_owned` imports you must set `ownership_attested=true` (you own a legal copy). Prefer public-domain sources (e.g. Project Gutenberg) with `license_kind=public_domain`.

### Playbooks & frameworks (L2–L3)

- `skill_playbook_list` / `skill_playbook_start` / `skill_playbook_next`
- `skill_framework_list` / `skill_framework_apply`

### Mentor / tutor (L4)

- `tutor_start` — `mode`: `socratic` | `avicenna` | `explain` | `quiz` | `coach`
- `tutor_turn` — next teaching move + suggested reply
- `tutor_record_mastery` — 0–1 scores; advances curriculum
- `skill_grade` — rubric scoring

### Prompts

- Socratic tutor prompt
- Avicenna tutor prompt
- Book-lens review prompt

## Example agent flows

**Socratic tutor**

1. `tutor_start(book_id="socratic-method", mode="socratic")`
2. Speak the `primary_question` to the user
3. `tutor_turn(session_id, learner_message=...)`
4. `tutor_record_mastery(...)` when ready

**Avicenna-mode**

1. `tutor_start(book_id="avicenna-canon", mode="avicenna")`
2. Demand genus + differentia; then division; then proof; then application
3. Never give clinical advice — historical framing only

**Book as review lens**

1. `skill_match(task="review this API design")`
2. `skill_framework_apply(...)`
3. `skill_search` + `skill_cite`
4. `skill_grade`

**Import your book**

Copy the file into `data/uploads/` (or set `BOOK_EXTRA_IMPORT_ROOT` to your books folder), then:

```text
skill_import_file(
  path="data/uploads/my-handbook.epub",
  title="My Handbook",
  license_kind="user_owned",
  ownership_attested=true,
  domains="product,research"
)
```

Arbitrary paths outside the sandbox are rejected (path traversal protection).

## Skill package layout

```text
skills/my-book/
  SKILL.md              # human/agent card
  skill.json            # structured card
  RIGHTS.md             # license + full_text_allowed
  toc.json
  excerpts/index.json   # citable chunks
  playbooks/index.json
  frameworks/index.json
  rubrics/index.json
  curriculum/curriculum.json
```

Imported books land in `library/` with the same shape (auto-built L4 scaffolding).

## Copyright & ethics (please read)

- **Do not** use this project to pirate books or redistribute copyrighted full text.
- **User-owned** path: you attest you have rights to use a copy for personal agent tooling; the server still prefers short citations over dumps.
- **Public domain / open license**: mark correctly; demo skills are educational curation.
- **Avicenna package**: history of ideas / method training — **not medicine**.
- **Socratic package**: dignity first; stop questioning in crisis or when the user needs direct facts.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Smoke without a host:

```bash
python -c "from book_skills_mcp.store import Library; print([p.card.id for p in Library().list_packages()])"
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CHANGELOG.md](CHANGELOG.md).

## Roadmap (good first issues)

- [ ] Embeddings backend (optional) behind the same `skill_search` API
- [ ] Community skill registry (share *methods*, not illegal full text)
- [ ] EPUB chapter-aware segmentation
- [ ] Export skill zip for sharing
- [ ] HTTP transport for multi-user installs (needs auth — see SECURITY.md)

## License

MIT — see [LICENSE](LICENSE). Bundled educational skill content is public-domain tradition + original curation; see each skill’s `RIGHTS.md`.
