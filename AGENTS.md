# Book Skills MCP — agent notes

## Project

MCP server that turns books into L0–L4 skill packages for agents.

- Package: `src/book_skills_mcp/`
- Bundled skills: `skills/avicenna-canon`, `skills/socratic-method`
- User imports: `library/`
- Sessions: `sessions/`

## Rules

- Log to **stderr only** (stdio MCP).
- Never invent book quotations — use `skill_search` / `skill_cite`.
- `user_owned` imports require `ownership_attested=true`.
- Avicenna skill is **not medical advice**.
- Socratic skill: dignity first; stop in crisis.

## Verify

```bash
pip install -e ".[dev]"
pytest
python -c "from book_skills_mcp.store import Library; print([p.card.id for p in Library().list_packages()])"
```
