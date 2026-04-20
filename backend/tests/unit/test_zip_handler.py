"""Unit tests for zip_handler: extraction, recursion, ZIP-Slip protection."""
import zipfile
from pathlib import Path

import pytest


def _make_zip(dest: Path, entries: dict[str, bytes]) -> Path:
    """Create a ZIP file at *dest* with the given {name: content} entries."""
    with zipfile.ZipFile(str(dest), "w") as zf:
        for name, content in entries.items():
            zf.writestr(name, content)
    return dest


def test_extract_flat_zip(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    zip_path = _make_zip(tmp_path / "flat.zip", {"a.txt": b"hello", "b.txt": b"world"})
    flat, warnings = expand_zips([zip_path], tmp_path)

    names = {p.name for p in flat}
    assert "a.txt" in names
    assert "b.txt" in names
    assert len(warnings) == 0


def test_nested_zip_extracted(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    inner_zip_path = tmp_path / "inner.zip"
    _make_zip(inner_zip_path, {"nested.txt": b"deep content"})

    outer_zip_path = tmp_path / "outer.zip"
    with zipfile.ZipFile(str(outer_zip_path), "w") as zf:
        zf.write(str(inner_zip_path), "inner.zip")
        zf.writestr("top.txt", b"top level")

    flat, warnings = expand_zips([outer_zip_path], tmp_path)
    names = {p.name for p in flat}
    assert "nested.txt" in names
    assert "top.txt" in names


def test_max_depth_respected(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    # Build a 3-level deep nested ZIP
    level3 = tmp_path / "l3.zip"
    _make_zip(level3, {"deep.txt": b"very deep"})

    level2 = tmp_path / "l2.zip"
    with zipfile.ZipFile(str(level2), "w") as zf:
        zf.write(str(level3), "l3.zip")

    level1 = tmp_path / "l1.zip"
    with zipfile.ZipFile(str(level1), "w") as zf:
        zf.write(str(level2), "l2.zip")

    # max_depth=1 should stop after the first level
    flat, warnings = expand_zips([level1], tmp_path, max_depth=1)
    names = {p.name for p in flat}
    # l2.zip would be extracted, but then skipped due to depth limit
    assert any("max nesting depth" in w for w in warnings)
    assert "deep.txt" not in names


def test_zip_slip_blocked(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    # Craft a malicious ZIP with a path traversal entry
    malicious_zip = tmp_path / "malicious.zip"
    with zipfile.ZipFile(str(malicious_zip), "w") as zf:
        # This would escape the destination directory
        zf.writestr("../../evil.txt", b"evil content")

    flat, warnings = expand_zips([malicious_zip], tmp_path)
    # The malicious entry must be blocked
    assert any("ZIP-Slip" in w for w in warnings)
    # The evil file must NOT have been written outside tmp_path
    evil = tmp_path.parent / "evil.txt"
    assert not evil.exists()


def test_macosx_entries_skipped(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    zip_path = tmp_path / "mac.zip"
    with zipfile.ZipFile(str(zip_path), "w") as zf:
        zf.writestr("__MACOSX/._real.txt", b"mac metadata")
        zf.writestr("real.txt", b"real content")

    flat, warnings = expand_zips([zip_path], tmp_path)
    names = {p.name for p in flat}
    assert "real.txt" in names
    assert "._real.txt" not in names


def test_corrupt_zip_returns_warning(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"this is not a zip file at all")

    flat, warnings = expand_zips([bad_zip], tmp_path)
    assert len(flat) == 0
    assert any("bad.zip" in w for w in warnings)


def test_non_zip_files_pass_through(tmp_path: Path):
    from app.services.zip_handler import expand_zips

    txt = tmp_path / "plain.txt"
    txt.write_bytes(b"just text")

    flat, warnings = expand_zips([txt], tmp_path)
    assert flat == [txt]
    assert len(warnings) == 0
