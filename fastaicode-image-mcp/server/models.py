from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedImageResponse:
    created: int | None
    revised_prompt: str | None
    image_bytes: bytes
