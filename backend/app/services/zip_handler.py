"""
ZIP file handler with recursive extraction and ZIP-Slip protection.
"""
import logging
import zipfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Files/dirs to skip when extracting
_SKIP_PATTERNS: tuple[str, ...] = (
    "__MACOSX",
    ".DS_Store",
    "Thumbs.db",
    "desktop.ini",
)


def expand_zips(
    paths: list[Path],
    dest_dir: Path,
    max_depth: int = 5,
    _current_depth: int = 0,
    _source_archive: str | None = None,
) -> tuple[list[Path], list[str]]:
    """
    Recursively expand any ZIP files found in *paths*.

    ZIP-Slip protection: any entry whose resolved path escapes *dest_dir* is
    skipped with a warning (never extracted).

    Args:
        paths:          List of file paths to process (mix of ZIPs and non-ZIPs).
        dest_dir:       Root directory under which all extracted files must land.
        max_depth:      Maximum nesting depth for nested ZIPs.
        _current_depth: Internal recursion counter.
        _source_archive: Internal — name of the parent ZIP, for provenance.

    Returns:
        (flat_files, warnings)
        flat_files: All non-ZIP files after recursive extraction.
        warnings:   Any non-fatal issues encountered.
    """
    flat: list[Path] = []
    warnings: list[str] = []

    for path in paths:
        if not _should_process(path):
            continue

        if not _is_zip(path):
            flat.append(path)
            continue

        # ── It's a ZIP ────────────────────────────────────────────────────────
        if _current_depth >= max_depth:
            warnings.append(
                f"Skipped nested ZIP '{path.name}': max nesting depth ({max_depth}) reached."
            )
            continue

        archive_name = _source_archive or path.name
        extract_dir = dest_dir / f"_extracted_{path.stem}_{_current_depth}"
        extract_dir.mkdir(parents=True, exist_ok=True)

        extracted_paths, zip_warnings = _extract_zip(path, extract_dir)
        warnings.extend(zip_warnings)

        # Recurse into any newly extracted files (handles nested ZIPs)
        sub_flat, sub_warnings = expand_zips(
            extracted_paths,
            dest_dir,
            max_depth=max_depth,
            _current_depth=_current_depth + 1,
            _source_archive=archive_name,
        )
        flat.extend(sub_flat)
        warnings.extend(sub_warnings)

        # Attach source_archive info as a sidecar attribute for provenance
        for f in sub_flat:
            if not hasattr(f, "_source_archive"):
                try:
                    object.__setattr__(f, "_source_archive", archive_name)
                except (AttributeError, TypeError):
                    pass  # Path objects don't support arbitrary attributes; ignored

    return flat, warnings


def _is_zip(path: Path) -> bool:
    """Return True if *path* looks like a ZIP archive."""
    if path.suffix.lower() == ".zip":
        return True
    try:
        return zipfile.is_zipfile(str(path))
    except (OSError, ValueError):
        return False


def _should_process(path: Path) -> bool:
    """Return False for OS metadata files that should always be ignored."""
    parts = path.parts
    for part in parts:
        if any(skip in part for skip in _SKIP_PATTERNS):
            return False
    return True


def _extract_zip(
    zip_path: Path,
    dest_dir: Path,
) -> tuple[list[Path], list[str]]:
    """
    Extract a single ZIP file into *dest_dir* with ZIP-Slip protection.

    Returns (extracted_paths, warnings).
    """
    extracted: list[Path] = []
    warnings: list[str] = []

    if not zipfile.is_zipfile(str(zip_path)):
        warnings.append(f"File '{zip_path.name}' has .zip extension but is not a valid ZIP.")
        return extracted, warnings

    try:
        with zipfile.ZipFile(str(zip_path), "r") as zf:
            # Detect password-protected archives before iterating
            for info in zf.infolist():
                if info.flag_bits & 0x1:
                    warnings.append(
                        f"Skipped '{zip_path.name}': archive is password-protected."
                    )
                    return extracted, warnings

            for info in zf.infolist():
                entry_name = info.filename

                # Skip directory entries
                if entry_name.endswith("/"):
                    continue

                # Skip OS metadata
                if not _should_process(Path(entry_name)):
                    continue

                # ZIP-Slip protection
                dest_path = (dest_dir / entry_name).resolve()
                if not str(dest_path).startswith(str(dest_dir.resolve())):
                    warnings.append(
                        f"ZIP-Slip attempt blocked: entry '{entry_name}' in "
                        f"'{zip_path.name}' would escape extraction directory."
                    )
                    logger.warning(
                        "ZIP-Slip blocked: '%s' in '%s'", entry_name, zip_path.name
                    )
                    continue

                dest_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with zf.open(info) as src, dest_path.open("wb") as dst:
                        dst.write(src.read())
                    extracted.append(dest_path)
                except Exception as exc:  # noqa: BLE001
                    warnings.append(
                        f"Could not extract '{entry_name}' from '{zip_path.name}': {exc}"
                    )

    except zipfile.BadZipFile as exc:
        warnings.append(f"Corrupt ZIP file '{zip_path.name}': {exc}")
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Unexpected error extracting '{zip_path.name}': {exc}")

    logger.info(
        "Extracted %d files from '%s' → %s", len(extracted), zip_path.name, dest_dir
    )
    return extracted, warnings
