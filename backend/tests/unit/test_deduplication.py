"""Unit tests for SHA-256 deduplication."""
from pathlib import Path

import pytest


def test_unique_files_all_returned(tmp_path: Path):
    from app.services.deduplication import deduplicate

    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_bytes(b"content alpha")
    b.write_bytes(b"content beta")

    unique, warnings = deduplicate([a, b])
    assert len(unique) == 2
    assert len(warnings) == 0


def test_duplicate_file_removed(tmp_path: Path):
    from app.services.deduplication import deduplicate

    a = tmp_path / "original.txt"
    b = tmp_path / "copy.txt"
    a.write_bytes(b"identical content")
    b.write_bytes(b"identical content")

    unique, warnings = deduplicate([a, b])
    assert len(unique) == 1
    assert unique[0] == a
    assert len(warnings) == 1
    assert "copy.txt" in warnings[0]


def test_order_preserved_for_unique(tmp_path: Path):
    from app.services.deduplication import deduplicate

    files = []
    for i in range(5):
        p = tmp_path / f"file{i}.txt"
        p.write_bytes(f"content {i}".encode())
        files.append(p)

    unique, warnings = deduplicate(files)
    assert unique == files
    assert len(warnings) == 0


def test_all_duplicates_of_same_file(tmp_path: Path):
    from app.services.deduplication import deduplicate

    paths = []
    for i in range(4):
        p = tmp_path / f"dup{i}.txt"
        p.write_bytes(b"same bytes")
        paths.append(p)

    unique, warnings = deduplicate(paths)
    assert len(unique) == 1
    assert len(warnings) == 3


def test_empty_list(tmp_path: Path):
    from app.services.deduplication import deduplicate

    unique, warnings = deduplicate([])
    assert unique == []
    assert warnings == []
