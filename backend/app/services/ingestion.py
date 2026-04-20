import json
from pathlib import Path

from app.config import settings

_EXTRACTED_FILENAME = "extracted.json"
_CLASSIFICATIONS_FILENAME = "classifications.json"
_FIELDS_FILENAME = "fields.json"
_METADATA_FILENAME = "metadata.json"


def save_uploaded_files(job_id: str, file_payloads: list[tuple[str, bytes]]) -> list[Path]:
    """
    Persist uploaded file bytes under uploads/{job_id}/.
    Returns the list of saved file paths.
    """
    job_dir = Path(settings.upload_dir) / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    saved: list[Path] = []
    for filename, content in file_payloads:
        dest = job_dir / filename
        dest.write_bytes(content)
        saved.append(dest)

    return saved


def save_extracted_texts(job_id: str, texts: dict[str, str]) -> None:
    """Persist {filename: text} to uploads/{job_id}/extracted.json."""
    _write_json(job_id, _EXTRACTED_FILENAME, texts)


def load_extracted_texts(job_id: str) -> dict[str, str]:
    """Load extracted texts written by save_extracted_texts."""
    return _read_json(job_id, _EXTRACTED_FILENAME)


def save_classifications(job_id: str, classifications: dict) -> None:
    """
    Persist {filename: {document_type, confidence, notes}}
    to uploads/{job_id}/classifications.json.
    """
    _write_json(job_id, _CLASSIFICATIONS_FILENAME, classifications)


def load_classifications(job_id: str) -> dict:
    """Load classifications written by save_classifications."""
    return _read_json(job_id, _CLASSIFICATIONS_FILENAME)


def save_fields(job_id: str, fields: dict) -> None:
    """
    Persist {document_type: {field: value, ...}}
    to uploads/{job_id}/fields.json.
    """
    _write_json(job_id, _FIELDS_FILENAME, fields)


def load_fields(job_id: str) -> dict:
    """Load extracted fields written by save_fields."""
    return _read_json(job_id, _FIELDS_FILENAME)


def save_parsed_metadata(job_id: str, metadata: dict) -> None:
    """
    Persist per-file ingestion metadata (file_type, extraction_method, warnings,
    sha256, source_archive) to uploads/{job_id}/metadata.json.
    """
    _write_json(job_id, _METADATA_FILENAME, metadata)


def load_parsed_metadata(job_id: str) -> dict:
    """Load metadata written by save_parsed_metadata."""
    return _read_json(job_id, _METADATA_FILENAME)


# ── internal helpers ───────────────────────────────────────────────────────────

def _write_json(job_id: str, filename: str, data: dict) -> None:
    dest = Path(settings.upload_dir) / job_id / filename
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def save_report(job_id: str, report: dict) -> None:
    """Persist the final report dict to uploads/{job_id}/report.json."""
    _write_json(job_id, "report.json", report)


def load_report(job_id: str) -> dict:
    """Load report saved by save_report."""
    return _read_json(job_id, "report.json")


def _read_json(job_id: str, filename: str) -> dict:
    src = Path(settings.upload_dir) / job_id / filename
    if not src.exists():
        return {}
    return json.loads(src.read_text(encoding="utf-8"))
