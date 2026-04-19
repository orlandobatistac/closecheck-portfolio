"""
Anthropic SDK wrapper with retry logic and JSON parsing helper.
All LLM calls go through here so it's easy to swap models or add caching.
"""
import json
import logging
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.Anthropic | None = None


class ClaudeResponseError(RuntimeError):
    """Raised when Claude returns a response that cannot be parsed or is structurally invalid."""


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def claude_json(prompt: str, max_tokens: int = 1024) -> dict[str, Any]:
    """
    Send a prompt to Claude and parse the response as JSON.
    Expects Claude to return a JSON object (no markdown fences).
    Raises ClaudeResponseError if the response is not valid JSON.
    """
    client = get_client()
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        stream=False,
        messages=[{"role": "user", "content": prompt}],
        system=(
            "You are a real estate document analysis expert. "
            "Always respond with valid JSON only — no markdown, no explanation."
        ),
    )
    # SDK ≥0.40 may include ThinkingBlock entries before the TextBlock
    text_block = next((b for b in message.content if hasattr(b, "text")), None)
    if text_block is None:
        raise ClaudeResponseError(
            f"Claude response contained no text block. "
            f"Block types received: {[type(b).__name__ for b in message.content]}"
        )
    raw = text_block.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ClaudeResponseError(
            f"Claude returned an invalid JSON response and cannot be parsed. "
            f"Check the prompt template or model output. "
            f"Raw response (first 200 chars): {raw[:200]!r}. "
            f"Parser error: {exc}"
        ) from exc


def claude_text(prompt: str, system: str = "", max_tokens: int = 2048) -> str:
    """Send a prompt and return raw text response."""
    client = get_client()
    message = client.messages.create(
        model=settings.claude_model,
        max_tokens=max_tokens,
        stream=False,
        messages=[{"role": "user", "content": prompt}],
        **({"system": system} if system else {}),
    )
    text_block = next((b for b in message.content if hasattr(b, "text")), None)
    if text_block is None:
        raise ClaudeResponseError("Claude response contained no text block.")
    return text_block.text.strip()

