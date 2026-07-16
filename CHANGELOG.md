# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-07-16

### Ship improvements (why upgrade)

Not a title tweak — **agent-callable product depth** pressure-tested with the bundled Avicenna and Socratic skills:

- **Definition that ships** — genus + differentia in server instructions (method package ≠ raw RAG)
- **Framework context seeds `subject` / `claim`** so worksheets start filled, not empty
- **Skill match that routes** — intent boosts for Socratic / Avicenna / tutor / playbook
- **Tutor claim focus** — elenchus quotes the learner’s sentence
- **Genre honesty** — novels stay L0–L1; method handbooks get L4 scaffolding
- **Transfer test** — `skill_transfer_test` + playbook *transfer* step (fresh particular)
- **What-to-expect examples** + infographics for real tool sequences
- **Pinned dependencies** — `requirements.txt` / floors aligned to current PyPI (mcp 1.28+)
- **20 automated tests** including full book-challenge suite

### Added

- `skill_transfer_test` MCP tool
- `classify_genre` / `TextGenre` on import packages
- `docs/examples/*` walkthroughs + challenge write-up
- SVG + hero “what to expect” assets
- Compatible hosts: Cursor, Claude, VS Code, Google Antigravity, Zed, Cline, Continue, JetBrains

### Fixed

- Framework `context=` only seeded a field named `context` (Avicenna `subject` stayed empty)
- Weak `skill_match` ranking for method demos
- Tutor turns ignored learner claims
- Narrative imports no longer claim false L4 playbooks

### Security

- Path sandbox, SSRF guards, untrusted excerpt labels (from 0.1.x) retained
- No API keys required for local operation

## [0.1.0] — 2026-07-16

### Added

- **Book Guide MCP** public open-source release: use your books as guides for AI agents.
- MCP server with L0–L4 book skill tools (library, search/cite, playbooks, frameworks, tutor, rubrics).
- Bundled demo skills: `socratic-method`, `avicenna-canon` (educational, not medical advice).
- Import from local files (sandboxed) and public http(s) URLs (SSRF-guarded).
- Tutor modes: `socratic`, `avicenna`, `explain`, `quiz`, `coach`.
- Untrusted-content labeling on excerpts and search snippets.
- Agent-oriented README, SECURITY, CONTRIBUTING, CI workflow (MIT).

### Security

- Path sandbox for `skill_import_file` (roots via env).
- SSRF protections: private IP / metadata / localhost blocked; redirects re-validated.
- Download size and extracted text caps.
- No API keys required for default local operation.
