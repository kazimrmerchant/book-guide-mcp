# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-07-16

### Added

- MCP server with L0–L4 book skill tools (library, search/cite, playbooks, frameworks, tutor, rubrics).
- Bundled demo skills: `socratic-method`, `avicenna-canon` (educational, not medical advice).
- Import from local files (sandboxed) and public http(s) URLs (SSRF-guarded).
- Tutor modes: `socratic`, `avicenna`, `explain`, `quiz`, `coach`.
- Untrusted-content labeling on excerpts and search snippets.
- MIT license, CONTRIBUTING, SECURITY, CI workflow.

### Security

- Path sandbox for `skill_import_file` (roots via env).
- SSRF protections: private IP / metadata / localhost blocked; redirects re-validated.
- Download size and extracted text caps.
