"""
CSV extractor — stdlib csv.reader with encoding auto-detection.
"""
import csv
import io
import logging
from pathlib import Path

from app.services.extractors import BaseExtractor, ParsedDocument, compute_sha256

logger = logging.getLogger(__name__)

_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")


class CSVExtractor(BaseExtractor):

    def extract(self, path: Path) -> ParsedDocument:
        sha = compute_sha256(path)
        warnings: list[str] = []
        raw_bytes = path.read_bytes()

        # Try encodings in order until one decodes successfully
        text_content: str | None = None
        used_encoding = "utf-8"
        for enc in _ENCODINGS:
            try:
                text_content = raw_bytes.decode(enc)
                used_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        if text_content is None:
            text_content = raw_bytes.decode("utf-8", errors="replace")
            used_encoding = "utf-8 (lossy)"
            warnings.append("CSV encoding could not be determined; decoded with replacement characters.")

        # Detect delimiter
        try:
            dialect = csv.Sniffer().sniff(text_content[:4096], delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel  # default comma
            if path.suffix.lower() == ".tsv":
                dialect = csv.excel_tab

        try:
            reader = csv.reader(io.StringIO(text_content), dialect)
            rows = list(reader)
        except Exception as exc:  # noqa: BLE001
            return ParsedDocument(
                filename=path.name,
                file_type="csv",
                text=text_content,  # fall back to raw text
                extraction_method="raw",
                warnings=[f"CSV parsing failed, returned raw text: {exc}"],
                sha256=sha,
            )

        # Reconstruct as clean comma-separated text
        lines = [",".join(cell.strip() for cell in row) for row in rows if any(cell.strip() for cell in row)]

        return ParsedDocument(
            filename=path.name,
            file_type="csv",
            text="\n".join(lines).strip(),
            metadata={"row_count": len(rows), "encoding": used_encoding},
            extraction_method="native",
            warnings=warnings,
            sha256=sha,
        )
