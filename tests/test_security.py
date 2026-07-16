from __future__ import annotations

from pathlib import Path

import pytest

from book_skills_mcp.builder import import_file
from book_skills_mcp.models import LicenseKind
from book_skills_mcp.security import (
    assert_public_http_url,
    is_private_or_local_ip,
    label_untrusted,
    resolve_under_roots,
)
from book_skills_mcp.store import Library

ROOT = Path(__file__).resolve().parents[1]


def test_private_ips_detected():
    assert is_private_or_local_ip("127.0.0.1")
    assert is_private_or_local_ip("10.0.0.1")
    assert is_private_or_local_ip("192.168.1.1")
    assert is_private_or_local_ip("169.254.169.254")
    assert is_private_or_local_ip("::1")
    assert not is_private_or_local_ip("8.8.8.8")


def test_ssrf_blocks_localhost_and_metadata():
    with pytest.raises(ValueError, match="Refusing|localhost|private"):
        assert_public_http_url("http://127.0.0.1/secret")
    with pytest.raises(ValueError):
        assert_public_http_url("http://localhost/x")
    with pytest.raises(ValueError):
        assert_public_http_url("http://169.254.169.254/latest/meta-data/")
    with pytest.raises(ValueError):
        assert_public_http_url("http://user:pass@example.com/")
    with pytest.raises(ValueError):
        assert_public_http_url("file:///etc/passwd")


def test_path_sandbox_blocks_escape(tmp_path: Path):
    root = tmp_path / "uploads"
    root.mkdir()
    good = root / "book.md"
    good.write_text("# Hi\n\ncontent " * 20, encoding="utf-8")
    assert resolve_under_roots(good, [root]) == good.resolve()
    outside = tmp_path / "outside.md"
    outside.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="sandbox"):
        resolve_under_roots(outside, [root])
    with pytest.raises(ValueError, match="sandbox"):
        resolve_under_roots(root / ".." / "outside.md", [root])


def test_import_file_respects_sandbox(tmp_path: Path):
    lib = Library(
        skills_dir=tmp_path / "skills",
        library_dir=tmp_path / "library",
        sessions_dir=tmp_path / "sessions",
        extra_skill_dirs=[],
    )
    outside = tmp_path / "secret.md"
    outside.write_text("# Secret\n\n" + ("word " * 50), encoding="utf-8")
    with pytest.raises((ValueError, FileNotFoundError)):
        import_file(
            lib,
            outside,
            ownership_attested=True,
            license_kind=LicenseKind.USER_OWNED,
            sandbox_roots=[tmp_path / "uploads"],
        )
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    good = uploads / "ok.md"
    good.write_text("# Ok\n\n" + ("word " * 50), encoding="utf-8")
    pkg = import_file(
        lib,
        good,
        title="Ok Book",
        ownership_attested=True,
        license_kind=LicenseKind.USER_OWNED,
        sandbox_roots=[uploads],
        book_id="ok-book",
    )
    assert pkg.card.id == "ok-book"


def test_label_untrusted_strips_zwc():
    text = "hello\u200b world"
    labeled = label_untrusted("test", text)
    assert "\u200b" not in labeled
    assert "UNTRUSTED" in labeled
    assert "BEGIN EXTERNAL CONTENT" in labeled


def test_examples_importable_via_default_sandbox():
    """examples/ is in default sandbox so sample_book.md works in docs."""
    sample = ROOT / "examples" / "sample_book.md"
    assert sample.exists()
    lib = Library(
        skills_dir=ROOT / "src" / "book_skills_mcp" / "bundled_skills",
        library_dir=ROOT / "library",
        sessions_dir=ROOT / "sessions",
    )
    # May already exist from prior runs — use unique id
    pkg = import_file(
        lib,
        sample,
        title="Talking to Users Sample",
        ownership_attested=True,
        license_kind=LicenseKind.USER_OWNED,
        book_id="talking-to-users-sample",
        domains=["product"],
    )
    assert pkg.excerpts
