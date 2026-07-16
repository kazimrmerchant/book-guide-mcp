# Security Policy

**Book Guide MCP** is designed for local, user-controlled use. Default operation requires **no API keys or cloud credentials**.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Threat model (summary)

This MCP server runs **locally** under the user’s account and can:

- Read files **inside configured import sandboxes**
- Fetch **public http(s) URLs** (size-capped)
- Write skill packages under `library/` and sessions under `sessions/`

An LLM client may be steered by untrusted book/web text. We therefore:

- Sandbox filesystem imports
- Block SSRF to private/link-local/metadata addresses
- Label excerpts as untrusted content
- Cap download and extract sizes

## Reporting a vulnerability

Please report security issues **privately** (GitHub Security Advisory when the repo is public, or email the maintainer listed on the GitHub profile).

Include:

- Impact (e.g. read `~/.ssh`, hit cloud metadata)
- Reproduction steps
- Affected commit / version

We aim to acknowledge within 7 days.

## Non-goals / out of scope

- Piracy / copyright infringement by end users
- Jailbreaks of the host LLM itself
- Issues that require the user to intentionally set `BOOK_IMPORT_ROOTS` to their entire home directory

## Hardening tips for operators

- Keep `BOOK_IMPORT_ROOTS` narrow
- Do not point the sandbox at `$HOME` or system directories
- Prefer public-domain imports over random web pages
- Run the MCP only in trusted host applications
