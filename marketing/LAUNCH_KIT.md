# Book Guide MCP — launch kit

**Product:** Book Guide MCP  
**Tagline:** Use your books as guides for AI agents  
**URL:** https://github.com/kazimrmerchant/book-guide-mcp  
**License:** MIT · **Price:** Free / open source  
**One-liner:** Methods first. Full text second. Citations always.

---

## Product Hunt (submit as maker)

Product Hunt **cannot be fully automated** (personal login + Submit flow). Use this copy.

### Post fields

| Field | Copy |
|-------|------|
| **Name** | Book Guide MCP |
| **Tagline** (≤60 chars) | Use your books as guides for AI agents |
| **URL** | https://github.com/kazimrmerchant/book-guide-mcp |
| **Topics / tags** | Artificial Intelligence, Open Source, Developer Tools, Education, Productivity |
| **Pricing** | Free |
| **Description** (≤260 chars) | Open-source MCP server that turns books you own into agent skills: cited search, playbooks, frameworks, and Socratic/Avicenna tutors. Works with Cursor, Claude, VS Code, Google Antigravity, Zed & more. Local-first, no API keys. |

### First maker comment (post immediately after launch)

```text
Hey Product Hunt 👋

I built Book Guide MCP because agents keep inventing “best practices” while our shelves already hold the real methods.

What it does:
• Import a book you own (or a public-domain URL) → skill package
• L0–L4: search/cite → guide card → playbooks → frameworks → mentor tutors
• Socratic + Avicenna teaching modes for agents
• Runs locally over MCP stdio — Cursor, Claude Desktop/Code, VS Code, Google Antigravity, Zed, Cline, Continue, JetBrains

Not another RAG chat: methods first, citations always, no API keys required.

Repo: https://github.com/kazimrmerchant/book-guide-mcp
Would love feedback from agent builders and educators!
```

### Gallery assets (repo)

- `docs/assets/book-guide-infographic.svg` — primary infographic  
- `docs/assets/book-guide-infographic-hero.png` — hero still  
- `docs/assets/book-guide-infographic-alt.png` — alternate  

### How to submit (you)

1. Log in at https://www.producthunt.com (personal account)  
2. **Submit** → **New product** → paste the GitHub URL  
3. Paste tagline, description, Free pricing  
4. Upload gallery images from `docs/assets/`  
5. Schedule **Tue/Wed 12:01 AM PT** or launch now  
6. Post the maker comment above  

Official guide: https://www.producthunt.com/launch

---

## MCP / agent directories

| Directory | Action | Status notes |
|-----------|--------|--------------|
| **GitHub topics** | Already set (`mcp`, `cursor`, `google-antigravity`, …) | Done |
| **Glama** | Auto-indexes repos with `mcp` topics | Should appear after crawl |
| **PulseMCP** | Often syncs from registry + GitHub | After registry/topics |
| **Official MCP Registry** | Needs published package (PyPI) + `server.json` | Kit ready — publish PyPI first |
| **mcp.so** | Manual form + GitHub URL | Submit at https://mcp.so |
| **Smithery** | Manual / dashboard | https://smithery.ai |
| **awesome-mcp-servers** | Community PR | Open PR (see below) |
| **Hacker News** | Show HN post | Optional: “Show HN: Book Guide MCP…” |
| **Reddit** | r/mcp, r/LocalLLaMA, r/CursorAI | Use short pitch below |

### Short pitch (directories / social)

```text
Book Guide MCP — open-source MCP that turns books you own into agent skills
(playbooks, citations, Socratic & Avicenna tutors). Local-first, no API keys.
Works with Cursor, Claude, VS Code, Google Antigravity, Zed, and any MCP host.
https://github.com/kazimrmerchant/book-guide-mcp
```

### Show HN title

```text
Show HN: Book Guide MCP – use your books as guides for AI agents
```

---

## Official MCP Registry (when PyPI is published)

1. `pip install build twine` and publish `book-skills-mcp` to PyPI  
2. Ensure README contains: `<!-- mcp-name: io.github.kazimrmerchant/book-guide-mcp -->`  
3. Install publisher: `npm i -g @modelcontextprotocol/publisher`  
4. From repo root: `mcp-publisher login github` then `mcp-publisher publish`  
5. Verify at https://registry.modelcontextprotocol.io  

See `server.json` in this folder.

---

## Checklist

- [x] Public GitHub repo + MIT + README + security  
- [x] Infographic assets  
- [x] Host compatibility named (incl. Google Antigravity)  
- [x] Launch copy + Product Hunt maker comment  
- [ ] You: Product Hunt Submit (login required)  
- [ ] You or agent: confirm Glama listing after crawl  
- [ ] Optional: PyPI + official MCP Registry  
- [ ] Optional: Show HN / social posts  
