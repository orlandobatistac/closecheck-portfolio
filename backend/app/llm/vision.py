"""
Claude Vision helper for OCR and image-based document extraction.
Sends image bytes as base64 to the Anthropic messages API.
"""
import base64
import logging
from pathlib import Path

from app.llm.client import get_client
from app.config import settings

logger = logging.getLogger(__name__)

_OCR_SYSTEM = (
    "You are a document OCR assistant. Extract all visible text from the provided image, "
    "preserving layout where possible. Return only the extracted text — no commentary, "
    "no markdown formatting, no explanations."
)

_MIME_MAP: dict[str, str] = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    # tiff/bmp not directly supported by Claude Vision; caller converts first
}


def claude_vision(image_bytes: bytes, mime_type: str = "image/png") -> str:
    """
    Send raw image bytes to Claude Vision and return extracted text.

    Args:
        image_bytes: Raw bytes of the image (PNG, JPEG, GIF, or WebP).
        mime_type:   MIME type string — must be one of: image/jpeg, image/png,
                     image/gif, image/webp.

    Returns:
        Extracted text string. Empty string on blank/unreadable images.
    """
    if not image_bytes:
        return ""

    b64 = base64.standard_b64encode(image_bytes).decode("ascii")

    client = get_client()
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=4096,
        system=_OCR_SYSTEM,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": "Extract all text from this image."},
                ],
            }
        ],
    )

    text_block = next((b for b in message.content if hasattr(b, "text")), None)
    if text_block is None:
        logger.warning("Claude Vision returned no text block")
        return ""
    return text_block.text.strip()


def image_path_to_claude_mime(path: Path) -> str:
    """Return a Claude-compatible MIME type for the given image path."""
    return _MIME_MAP.get(path.suffix.lower(), "image/png")
