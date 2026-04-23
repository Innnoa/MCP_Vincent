from __future__ import annotations

from pathlib import Path
import re


def build_output_path(
    output_root: Path,
    prompt: str,
    filename_hint: str | None,
    now_text: str,
) -> Path:
    slug_source = filename_hint or prompt
    slug = re.sub(r"[^a-z0-9]+", "-", slug_source.lower()).strip("-") or "image"
    slug = slug[:48]
    return output_root / f"{now_text}-{slug}.png"
