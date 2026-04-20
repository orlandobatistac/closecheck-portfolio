"""
JSON extractor — normalizes JSON to indented text for LLM consumption.
"""
import json
import logging
from pathlib import Path

from app.services.extractors import BaseExtractor, ParsedDocument, compute_sha256

logger = logging.getLogger(__name__)

# Maximum number of sample items shown when the root is a list
_LIST_SAMPLE_SIZE = 10


class JSONExtractor(BaseExtractor):

    def extract(self, path: Path) -> ParsedDocument:
        sha = compute_sha256(path)
        warnings: list[str] = []

        raw_bytes = path.read_bytes()
        for enc in ("utf-8-sig", "utf-8", "latin-1"):
            try:
                raw_str = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raw_str = raw_bytes.decode("utf-8", errors="replace")
            warnings.append("JSON encoding could not be determined; decoded with replacement characters.")

        try:
            data = json.loads(raw_str)
        except json.JSONDecodeError as exc:
            return ParsedDocument(
                filename=path.name,
                file_type="json",
                text=raw_str.strip(),
                extraction_method="raw",
                warnings=[f"Invalid JSON — returned raw text. Parser error: {exc}"],
                sha256=sha,
            )

        root_type = type(data).__name__
        item_count: int | None = None

        # For large lists, show schema + sample rows
        if isinstance(data, list):
            item_count = len(data)
            if item_count > _LIST_SAMPLE_SIZE:
                sample = data[:_LIST_SAMPLE_SIZE]
                warnings.append(
                    f"JSON array has {item_count} items; showing first {_LIST_SAMPLE_SIZE} for LLM context."
                )
                text = json.dumps(sample, ensure_ascii=False, indent=2)
            else:
                text = json.dumps(data, ensure_ascii=False, indent=2)
        else:
            text = json.dumps(data, ensure_ascii=False, indent=2)

        meta: dict = {"root_type": root_type}
        if item_count is not None:
            meta["item_count"] = item_count

        return ParsedDocument(
            filename=path.name,
            file_type="json",
            text=text,
            metadata=meta,
            extraction_method="native",
            warnings=warnings,
            sha256=sha,
        )
