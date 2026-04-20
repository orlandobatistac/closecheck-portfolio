"""
HTML extractor — BeautifulSoup with lxml backend.
Strips scripts, styles, and navigational noise; returns readable plain text.
"""
import logging
from pathlib import Path

from app.services.extractors import BaseExtractor, ParsedDocument, compute_sha256

logger = logging.getLogger(__name__)

_SKIP_TAGS = {"script", "style", "noscript", "head", "meta", "link", "iframe"}


class HTMLExtractor(BaseExtractor):

    def extract(self, path: Path) -> ParsedDocument:
        sha = compute_sha256(path)
        warnings: list[str] = []

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            return ParsedDocument(
                filename=path.name,
                file_type="html",
                text="",
                extraction_method="failed",
                warnings=["beautifulsoup4 is not installed."],
                sha256=sha,
            )

        # Detect encoding — try utf-8 then latin-1
        raw_bytes = path.read_bytes()
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                html_str = raw_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            html_str = raw_bytes.decode("utf-8", errors="replace")
            warnings.append("HTML encoding could not be determined; used UTF-8 with replacement.")

        try:
            soup = BeautifulSoup(html_str, "lxml")
        except Exception:
            # lxml not available or parse error; fall back to html.parser
            try:
                soup = BeautifulSoup(html_str, "html.parser")
                warnings.append("lxml not available — used html.parser as fallback.")
            except Exception as exc:  # noqa: BLE001
                return ParsedDocument(
                    filename=path.name,
                    file_type="html",
                    text="",
                    extraction_method="failed",
                    warnings=[f"HTML parse error: {exc}"],
                    sha256=sha,
                )

        # Read title before decomposing unwanted tags
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Remove unwanted tags
        for tag in soup.find_all(_SKIP_TAGS):
            tag.decompose()

        text = soup.get_text(separator="\n")
        # Collapse excessive blank lines
        lines = [line.strip() for line in text.splitlines()]
        cleaned = "\n".join(line for line in lines if line)

        return ParsedDocument(
            filename=path.name,
            file_type="html",
            text=cleaned,
            metadata={"title": title},
            extraction_method="native",
            warnings=warnings,
            sha256=sha,
        )
