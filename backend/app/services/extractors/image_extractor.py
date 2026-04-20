"""
Image extractor — Pillow for format normalization, then Claude Vision for OCR.

Supports: jpg, jpeg, png, gif, tiff, bmp, webp.
TIFF and BMP are converted to PNG before sending to Claude (not natively supported).
"""
import io
import logging
from pathlib import Path

from app.services.extractors import BaseExtractor, ParsedDocument, compute_sha256

logger = logging.getLogger(__name__)

# Claude Vision only accepts these MIME types
_CLAUDE_SUPPORTED_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_EXT_TO_MIME: dict[str, str] = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".tiff": "image/tiff",   # will be converted
    ".tif":  "image/tiff",
    ".bmp":  "image/bmp",    # will be converted
}


class ImageExtractor(BaseExtractor):

    def extract(self, path: Path) -> ParsedDocument:
        warnings: list[str] = []
        sha = compute_sha256(path)

        try:
            from PIL import Image
        except ImportError:
            return ParsedDocument(
                filename=path.name,
                file_type="image",
                text="",
                extraction_method="failed",
                warnings=["Pillow is not installed."],
                sha256=sha,
            )

        # Determine original MIME
        original_mime = _EXT_TO_MIME.get(path.suffix.lower(), "image/png")
        send_mime = original_mime if original_mime in _CLAUDE_SUPPORTED_MIMES else "image/png"

        try:
            img = Image.open(str(path))
            img.load()  # Force decode to catch corrupt files early
        except Exception as exc:  # noqa: BLE001
            return ParsedDocument(
                filename=path.name,
                file_type="image",
                text="",
                extraction_method="failed",
                warnings=[f"Cannot open image '{path.name}': {exc}"],
                sha256=sha,
            )

        width, height = img.size
        mode = img.mode

        # Convert to PNG for Claude if needed
        if original_mime not in _CLAUDE_SUPPORTED_MIMES:
            buf = io.BytesIO()
            rgb = img.convert("RGB") if img.mode in ("P", "RGBA", "LA", "L") else img
            rgb.save(buf, format="PNG")
            image_bytes = buf.getvalue()
            send_mime = "image/png"
            warnings.append(
                f"'{path.name}' converted from {original_mime} to PNG for OCR."
            )
        else:
            image_bytes = path.read_bytes()

        try:
            from app.llm.vision import claude_vision
            text = claude_vision(image_bytes, mime_type=send_mime)
        except Exception as exc:  # noqa: BLE001
            text = ""
            warnings.append(f"Claude Vision OCR failed: {exc}")

        return ParsedDocument(
            filename=path.name,
            file_type="image",
            text=text.strip(),
            metadata={"width": width, "height": height, "mode": mode},
            extraction_method="ocr-vision",
            warnings=warnings,
            sha256=sha,
        )
