# Complete review — Book Skills MCP (0.1.0)

**Date:** 2026-07-16  
**Scope:** Architecture, MCP design, security, packaging, git/OSS readiness, demos (Socratic + Avicenna)  
**Verdict:** **Ship-ready as alpha** after fixes applied in this pass. Good public launch candidate with clear follow-ups.

---

## Executive summary

| Area | Grade | Notes |
|------|-------|-------|
| Product concept | A | Clear differentiation vs RAG: methods/playbooks/tutors |
| MCP tool design | A− | Task-shaped tools; 19 tools is full but coherent |
| Security | B+ → A− | SSRF + path sandbox + untrusted labels **fixed** |
| Packaging | B → A− | Bundled skills in wheel; user data dir when installed |
| Tests | B+ | Core + security coverage; needs more async MCP integration later |
| Docs / OSS hygiene | A− | README, LICENSE, CONTRIBUTING, SECURITY, CI, CODE_OF_CONDUCT |
| Copyright model | A− | Attestation + citation caps; still user-enforced honesty |
| Demo skills | A | Socratic + Avicenna are strong launch demos |

---

## Architecture review

### What works well

1. **Progressive disclosure** — `skill_open` / skill card before full excerpts (matches Cursor skill patterns).
2. **Level model L0–L4** — maps cleanly to tools and package folders.
3. **Separation of modules** — `store`, `search`, `builder`, `playbooks`, `tutor`, `security`, `server`.
4. **Session persistence** — playbook/tutor JSON under `sessions/` enables multi-turn mentoring.
5. **No paid APIs required** — lexical search only; good for open-source default.

### Design risks (accepted for 0.1)

| Risk | Impact | Mitigation / follow-up |
|------|--------|------------------------|
| Auto-built skills from novels are weak L4 | Users expect magic | Document genre limits; improve classifier later |
| Lexical search only | Misses paraphrase queries | Optional embeddings backend (roadmap) |
| Host model does teaching prose | Quality depends on host LLM | Tutor tools return *moves*, not monologues — correct |
| 19 tools | Host routing noise | Strong `instructions` string; consider tool groups later |

---

## MCP best practices checklist

| Rule | Status |
|------|--------|
| Stdio: log to stderr only | Pass |
| Task-shaped tools (not REST mirrors) | Pass |
| Descriptions written for the model | Pass |
| Param length limits | Pass (tightened) |
| Annotations (`readOnlyHint`, etc.) | Pass |
| Errors as actionable JSON content | Pass (`{"error":...}`) |
| Result size discipline | Pass (caps, truncate) |
| No secrets in descriptors | Pass (no API keys) |
| Untrusted external content labeled | Pass (added) |
| Destructive honesty | Pass (imports not destructive; no shell) |

---

## Security review (MCP security checklist)

### Fixed in this review pass

1. **SSRF** — private/link-local/metadata IPs blocked; DNS resolve checked; credentials-in-URL blocked; redirects re-validated (no blind follow).
2. **Path traversal** — `skill_import_file` only under sandbox roots (`BOOK_IMPORT_ROOTS` / defaults).
3. **Untrusted content fencing** — search snippets + cites labeled.
4. **Resource caps** — download 8MB, text 2M chars, PDF page cap, excerpt count cap.
5. **Installed-package data path** — no longer writes “library” next to site-packages blindly; uses source tree or OS app data.

### Remaining residual risks

| Issue | Severity | Notes |
|-------|----------|-------|
| DNS rebinding race (TOCTOU) | Low–Med | Classic SSRF residual; mitigate later with connect-time pin |
| `BOOK_EXTRA_IMPORT_ROOT=$HOME` operator footgun | Med | Documented in SECURITY.md |
| EPUB/PDF parsers (untrusted files) | Med | Dependency risk; pin versions; prefer md/epub from trusted sources |
| Prompt injection via book text | Med | Labeled; host must still not “obey” book instructions |
| No rate limit on URL import | Low | Local stdio single-user; add if HTTP transport ships |

### Not applicable (stdio-only)

- HTTP Origin/DNS rebinding host checks, OAuth, session cookies — N/A until Streamable HTTP.

---

## Code quality

### Strengths

- Pydantic models for packages and sessions
- Explicit license enum + ownership attestation
- Demo skills fully populated (TOC, excerpts, playbooks, frameworks, rubrics, curriculum)
- Tests cover library load, tutor modes, import, SSRF, sandbox

### Issues found & fixed

| Issue | Fix |
|-------|-----|
| Weak localhost-only SSRF | Full private IP + resolve + redirect checks |
| Arbitrary path import | Sandbox roots |
| Skills not in wheel | `bundled_skills` + hatch include |
| Placeholder GitHub URLs | Updated project.urls (org name placeholder still OK) |
| Inline import in store | Removed |
| Missing OSS files | CHANGELOG, CONTRIBUTING, SECURITY, CI, CoC |

### Still open (non-blocking)

- `server.py` is large (~600 lines) — split tools by domain when growing
- `resource_card` reloads full Library each call — fine for alpha
- No lockfile yet (`uv.lock` / `requirements.txt` freeze) — add on first release tag
- GitHub org `book-skills-mcp` is a placeholder until you create the remote

---

## Git / open-source best practices

### Applied

- [x] MIT LICENSE  
- [x] README with install, tools, safety  
- [x] CONTRIBUTING + CODE_OF_CONDUCT  
- [x] SECURITY policy + threat model  
- [x] CHANGELOG (Keep a Changelog)  
- [x] CI matrix (Windows + Ubuntu, Py 3.11–3.13)  
- [x] `.gitignore` excludes venv, user library/sessions/uploads  
- [x] Semantic version 0.1.0  
- [x] **Standalone git repo** recommended (do not ship from monorepo root)

### Monorepo warning

This folder currently lives under `Projects/` which already has a git root. For open-source:

```text
Preferred: book-skills-mcp/ as its OWN git repository
Avoid:     committing this from the monorepo root (pulls unrelated noise)
```

Initialize with:

```powershell
cd book-skills-mcp
git init
git add .
git status   # confirm no .venv, no library dumps
git commit -m "Initial release: book skills MCP L0-L4 with Socratic and Avicenna demos"
```

Then create GitHub repo and `git remote add origin …`.

### Release checklist (first public tag)

1. `pytest` green on CI  
2. `pip install .` from clean venv; `python -m book_skills_mcp` starts  
3. Confirm bundled skills load without repo `skills/` checkout  
4. Tag `v0.1.0`  
5. Optional: `pip-audit` / Dependabot  

---

## Demo skills review

### `socratic-method` — excellent

- Ethical boundaries (`dialogue-ethics`, stop conditions)
- Playbook `elenchus-loop` matches classical structure
- Tutor mode integrates cleanly

### `avicenna-canon` — excellent with safety

- Clear non-clinical framing
- Method order is pedagogically distinctive (launch story)
- Historical medical excerpt is disclaimer-heavy (good)

---

## Tool inventory (19)

`library_list`, `library_reload`, `skill_match`, `skill_open`, `skill_search`, `skill_cite`,  
`skill_import_file`, `skill_import_url`,  
`skill_playbook_list`, `skill_playbook_start`, `skill_playbook_next`,  
`skill_framework_list`, `skill_framework_apply`,  
`tutor_start`, `tutor_turn`, `tutor_record_mastery`,  
`skill_grade`, `skill_curriculum`, `skill_status`

---

## Recommended next milestones

### v0.1.1 (hardening)

- Connect-time IP pin for SSRF  
- `uv.lock` or pinned requirements  
- MCP Inspector smoke script in CI  

### v0.2.0 (product)

- Skill zip export/import  
- Better auto-playbook extraction from headings  
- Optional embeddings search  

### v0.3.0 (community)

- Skill registry format + validation CLI  
- Example third-party skill template  

---

## Final recommendation

**Approve for public alpha** on GitHub as a **standalone repository**, after:

1. Confirm tests green (including security suite)  
2. `git init` only inside `book-skills-mcp/`  
3. Replace placeholder remote URL with your real org/user  
4. Do not commit user-imported books or sessions  

This project’s story is clear: **books as executable skills**, not RAG blobs — with Socratic and Avicenna demos that show the L4 mentor path immediately.
