"""Resolve data directories for the Book Skills MCP."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _is_editable_or_source_tree() -> bool:
    """True when running from a source checkout (pyproject next to package parent)."""
    root = Path(__file__).resolve().parents[2]
    return (root / "pyproject.toml").is_file() and (root / "src" / "book_skills_mcp").is_dir()


def package_root() -> Path:
    """Repo root in editable/source installs; otherwise a stable user data root."""
    if _is_editable_or_source_tree():
        return Path(__file__).resolve().parents[2]
    return user_data_root()


def user_data_root() -> Path:
    """Writable per-user data directory for library/sessions/uploads."""
    env = os.environ.get("BOOK_DATA_DIR")
    if env:
        return Path(env).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return (base / "book-skills-mcp").resolve()


def bundled_skills_dir() -> Path:
    """Skills shipped inside the installed package (wheel)."""
    return Path(__file__).resolve().parent / "bundled_skills"


def default_skills_dir() -> Path:
    env = os.environ.get("BOOK_SKILLS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    bundled = bundled_skills_dir()
    if bundled.is_dir() and any(bundled.iterdir()):
        return bundled
    if _is_editable_or_source_tree():
        dev = Path(__file__).resolve().parents[2] / "skills"
        if dev.is_dir():
            return dev
    return bundled


def default_library_dir() -> Path:
    env = os.environ.get("BOOK_LIBRARY_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return package_root() / "library"


def default_sessions_dir() -> Path:
    env = os.environ.get("BOOK_SESSIONS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return package_root() / "sessions"


def default_uploads_dir() -> Path:
    env = os.environ.get("BOOK_UPLOADS_DIR")
    if env:
        return Path(env).expanduser().resolve()
    return package_root() / "data" / "uploads"


def import_sandbox_roots() -> list[Path]:
    """Directories from which skill_import_file may read.

    Override with BOOK_IMPORT_ROOTS (os.pathsep-separated absolute paths).
    """
    env = os.environ.get("BOOK_IMPORT_ROOTS")
    if env:
        return [Path(p).expanduser().resolve() for p in env.split(os.pathsep) if p.strip()]
    roots = [
        default_uploads_dir(),
        default_library_dir(),
        default_skills_dir(),
        bundled_skills_dir(),
    ]
    if _is_editable_or_source_tree():
        root = Path(__file__).resolve().parents[2]
        roots.extend([root / "examples", root / "data", root / "skills"])
    extra = os.environ.get("BOOK_EXTRA_IMPORT_ROOT")
    if extra:
        roots.append(Path(extra).expanduser().resolve())
    seen: set[str] = set()
    out: list[Path] = []
    for r in roots:
        try:
            key = str(r.expanduser().resolve())
        except OSError:
            key = str(r)
        if key not in seen:
            seen.add(key)
            out.append(r)
    return out
