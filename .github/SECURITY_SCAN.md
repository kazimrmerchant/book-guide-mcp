# Pre-publish security scan checklist

Run before every public push:

- [ ] No `.env` with real values (only `.env.example` placeholders)
- [ ] No API keys, tokens, private keys in any tracked file
- [ ] `library/*` and `sessions/*` and `data/uploads/*` empty except `.gitkeep`
- [ ] `git grep -iE 'ghp_|sk-|api_key|BEGIN PRIVATE'` returns only docs/tests false positives
- [ ] `pytest` green including `tests/test_security.py`
