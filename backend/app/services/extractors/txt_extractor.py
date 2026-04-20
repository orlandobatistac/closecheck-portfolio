"""
Plain-text extractor with encoding auto-detection.
"""
import logging
from pathlib import Path

from app.services.extractors import BaseExtractor, ParsedDocument, compute_sha256

logger = logging.getLogger(__name__)

_ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")


class TXTExtractor(BaseExtractor):

    def extract(self, path: Path) -> ParsedDocument:
        sha = compute_sha256(path)
        warnings: list[str] = []
        raw_bytes = path.read_bytes()

        text: str | None = None
        used_encoding = "utf-8"
        for enc in _ENCODINGS:
            try:
                text = raw_bytes.decode(enc)
                used_encoding = enc
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            text = raw_bytes.decode("utf-8", errors="replace")
            used_encoding = "utf-8 (lossy)"
            warnings.append("Text encoding could not be determined; decoded with replacement characters.")

        return ParsedDocument(
            filename=path.name,
            file_type="txt",
            text=text.strip(),
            metadata={"encoding": used_encoding, "size_bytes": len(raw_bytes)},
            extraction_method="native",
            warnings=warnings,
            sha256=sha,
        )
