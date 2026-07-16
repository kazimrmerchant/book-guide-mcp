# Contributing to Book Guide MCP

Thanks for helping. **Book Guide MCP** ships as a **local stdio MCP server** so people can use their books as guides for AI agents.

## Development setup

```bash
git clone <your-fork-or-repo-url>
cd book-skills-mcp
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## Branch & commit hygiene

- Branch from `main`: `git switch -c fix/short-description`
- Small, focused commits; imperative subject (`Add SSRF check for redirects`)
- Do not commit `.venv/`, `library/*` user imports, `sessions/*`, secrets, or large binary books
- Do not commit copyrighted full-text books

## What makes a good PR

1. **Problem statement** — what was broken or missing
2. **Tests** — unit tests for logic; security tests for path/URL edges
3. **Docs** — README / CHANGELOG updated when user-visible
4. **No drive-by refactors**

## Skill packages

Bundled demos live in:

- `skills/` (source of truth for git)
- `src/book_skills_mcp/bundled_skills/` (copied into the wheel)

If you change a demo skill, update **both** trees (or re-copy before release).

New community skills should:

- Include `skill.json`, `RIGHTS.md`, and honest `license`
- Prefer methods/playbooks/excerpts over full copyrighted text
- Mark medical/legal content with strong safety notes

## Code style

- Python 3.11+
- Type hints on public functions
- Logging to **stderr only** (stdio MCP)
- Imports at module top (no inline imports)
- Prefer small modules over one giant `server.py` growth

## Security reports

See [SECURITY.md](SECURITY.md). Do not open public issues for exploitable SSRF/path bugs before a fix is ready.

## License

By contributing, you agree your contributions are licensed under the MIT License.
