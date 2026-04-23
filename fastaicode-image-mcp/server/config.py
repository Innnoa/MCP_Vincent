from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    default_model: str
    default_output_dir: Path
    size_preset_mapping: dict[str, str]
    request_timeout_seconds: float


def load_settings(config_file: Path) -> Settings:
    config_path = config_file.resolve()
    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    api_key = os.environ.get("FASTAICODE_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing FASTAICODE_API_KEY")

    base_url = os.environ.get("FASTAICODE_BASE_URL", raw["base_url"]).strip().rstrip("/")
    mapping = _normalize_mapping(raw.get("size_preset_mapping", {}))
    output_dir = Path(raw.get("default_output_dir", "outputs/images"))
    if not output_dir.is_absolute():
        output_dir = config_path.parent / output_dir

    return Settings(
        base_url=base_url,
        api_key=api_key,
        default_model=raw.get("default_model", "gpt-image-2"),
        default_output_dir=output_dir,
        size_preset_mapping=mapping,
        request_timeout_seconds=float(raw.get("request_timeout_seconds", 300)),
    )


def resolve_size_preset(size_preset: str, mapping: dict[str, str]) -> str:
    preset = size_preset.lower()
    if preset == "auto":
        return mapping.get("auto", "auto")
    if preset not in mapping:
        raise ValueError(f"Unsupported size preset: {size_preset}")
    return mapping[preset]


def _normalize_mapping(mapping: dict[str, str]) -> dict[str, str]:
    normalized = dict(mapping)
    aliases = {
        "one_k": "1k",
        "two_k": "2k",
        "four_k": "4k",
    }
    for source, target in aliases.items():
        if target not in normalized and source in normalized:
            normalized[target] = normalized[source]
    return normalized
