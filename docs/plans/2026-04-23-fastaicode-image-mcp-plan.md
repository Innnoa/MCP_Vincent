# FastAICode Image MCP Plugin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable local MCP plugin that lets Codex generate and edit images through the FastAICode API and automatically save decoded PNG files locally.

**Architecture:** The plugin lives in a self-contained `fastaicode-image-mcp/` directory with a Python MCP server, small focused modules for config, naming, API calls, and the MCP tool surface, plus a companion Skill that standardizes how the tools are used. The server exposes `generate_image` and `edit_image`, both of which read config, call the appropriate remote image API, decode `b64_json`, write a PNG, and return structured results.

**Tech Stack:** Python 3, MCP server runtime, `httpx`, `pytest`, TOML config parsing, Base64 decoding, multipart uploads, local Codex plugin metadata.

---

### Task 1: Bootstrap plugin layout and metadata

**Files:**
- Create: `fastaicode-image-mcp/.codex-plugin/plugin.json`
- Create: `fastaicode-image-mcp/server/__init__.py`
- Create: `fastaicode-image-mcp/server/mcp_server.py`
- Create: `fastaicode-image-mcp/pyproject.toml`
- Test: `fastaicode-image-mcp/tests/test_plugin_layout.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import json


def test_plugin_metadata_points_to_mcp_server():
    plugin_file = Path("fastaicode-image-mcp/.codex-plugin/plugin.json")
    data = json.loads(plugin_file.read_text(encoding="utf-8"))

    assert data["name"] == "fastaicode-image-mcp"
    assert "server" in data
    assert data["server"]["entrypoint"].endswith("server/mcp_server.py")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest fastaicode-image-mcp/tests/test_plugin_layout.py -v`
Expected: FAIL because plugin files do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```json
{
  "name": "fastaicode-image-mcp",
  "version": "0.1.0",
  "description": "Local MCP plugin for FastAICode image generation",
  "server": {
    "runtime": "python",
    "entrypoint": "server/mcp_server.py"
  }
}
```

```python
# server/__init__.py
__all__ = []
```

```python
# server/mcp_server.py
def main() -> None:
    raise SystemExit("MCP server not implemented yet")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest fastaicode-image-mcp/tests/test_plugin_layout.py -v`
Expected: PASS

### Task 2: Implement config loading, size preset resolution, and file naming

**Files:**
- Create: `fastaicode-image-mcp/server/config.py`
- Create: `fastaicode-image-mcp/server/naming.py`
- Create: `fastaicode-image-mcp/examples/fastaicode-image.example.toml`
- Test: `fastaicode-image-mcp/tests/test_config.py`
- Test: `fastaicode-image-mcp/tests/test_naming.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from server.config import load_settings, resolve_size_preset
from server.naming import build_output_path


def test_environment_base_url_overrides_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
base_url = "http://from-file.example"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"

[size_preset_mapping]
one_k = "1024x1024"
two_k = "auto"
        """.strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FASTAICODE_BASE_URL", "http://from-env.example")
    monkeypatch.setenv("FASTAICODE_API_KEY", "secret")

    settings = load_settings(config_file)

    assert settings.base_url == "http://from-env.example"


def test_resolve_four_k_requires_explicit_mapping():
    settings = {
        "1k": "1024x1024",
        "2k": "auto",
        "auto": "auto",
    }

    try:
        resolve_size_preset("4k", settings)
    except ValueError as exc:
        assert "4k" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_build_output_path_uses_timestamp_and_slug(tmp_path):
    path = build_output_path(
        output_root=tmp_path,
        prompt="a tiny red circle on a white background",
        filename_hint="red-circle",
        now_text="20260423-153000",
    )

    assert path.name == "20260423-153000-red-circle.png"
    assert path.parent == tmp_path
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest fastaicode-image-mcp/tests/test_config.py fastaicode-image-mcp/tests/test_naming.py -v`
Expected: FAIL because modules do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass
class Settings:
    base_url: str
    api_key: str
    default_model: str
    default_output_dir: Path
    size_preset_mapping: dict[str, str]
    request_timeout_seconds: float


def load_settings(config_file: Path) -> Settings:
    raw = tomllib.loads(config_file.read_text(encoding="utf-8"))
    api_key = os.environ.get("FASTAICODE_API_KEY", "")
    if not api_key:
        raise ValueError("Missing FASTAICODE_API_KEY")
    base_url = os.environ.get("FASTAICODE_BASE_URL", raw["base_url"])
    return Settings(
        base_url=base_url.rstrip("/"),
        api_key=api_key,
        default_model=raw.get("default_model", "gpt-image-2"),
        default_output_dir=Path(raw.get("default_output_dir", "outputs/images")),
        size_preset_mapping=_normalize_mapping(raw.get("size_preset_mapping", {})),
        request_timeout_seconds=float(raw.get("request_timeout_seconds", 60)),
    )


def _normalize_mapping(mapping: dict[str, str]) -> dict[str, str]:
    normalized = dict(mapping)
    if "1k" not in normalized and "one_k" in normalized:
        normalized["1k"] = normalized["one_k"]
    if "2k" not in normalized and "two_k" in normalized:
        normalized["2k"] = normalized["two_k"]
    return normalized


def resolve_size_preset(size_preset: str, mapping: dict[str, str]) -> str | None:
    preset = size_preset.lower()
    if preset == "auto":
        return mapping.get("auto", "auto")
    if preset not in mapping:
        raise ValueError(f"Unsupported size preset: {size_preset}")
    return mapping[preset]
```

```python
from pathlib import Path
import re


def build_output_path(output_root: Path, prompt: str, filename_hint: str | None, now_text: str) -> Path:
    slug_source = filename_hint or prompt
    slug = re.sub(r"[^a-z0-9]+", "-", slug_source.lower()).strip("-") or "image"
    slug = slug[:48]
    return output_root / f"{now_text}-{slug}.png"
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest fastaicode-image-mcp/tests/test_config.py fastaicode-image-mcp/tests/test_naming.py -v`
Expected: PASS

### Task 3: Implement API client and Base64 decoding pipeline

**Files:**
- Create: `fastaicode-image-mcp/server/client.py`
- Create: `fastaicode-image-mcp/server/models.py`
- Test: `fastaicode-image-mcp/tests/test_client.py`

- [ ] **Step 1: Write the failing tests**

```python
import base64
from pathlib import Path

from server.client import decode_and_save_png, parse_generation_payload


def test_parse_generation_payload_reads_b64_json():
    payload = {
        "created": 1776860842,
        "data": [
            {
                "b64_json": base64.b64encode(b"png-bytes").decode("ascii"),
                "revised_prompt": "clean prompt",
            }
        ],
    }

    result = parse_generation_payload(payload)

    assert result.created == 1776860842
    assert result.revised_prompt == "clean prompt"
    assert result.image_bytes == b"png-bytes"


def test_decode_and_save_png_writes_file(tmp_path):
    target = tmp_path / "image.png"

    decode_and_save_png(b"png-bytes", target)

    assert target.read_bytes() == b"png-bytes"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest fastaicode-image-mcp/tests/test_client.py -v`
Expected: FAIL because client helpers do not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
import base64
from pathlib import Path


@dataclass
class ParsedImageResponse:
    created: int | None
    revised_prompt: str | None
    image_bytes: bytes


def parse_generation_payload(payload: dict) -> ParsedImageResponse:
    try:
        first = payload["data"][0]
        encoded = first["b64_json"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("Response missing data[0].b64_json") from exc

    return ParsedImageResponse(
        created=payload.get("created"),
        revised_prompt=first.get("revised_prompt"),
        image_bytes=base64.b64decode(encoded),
    )


def decode_and_save_png(image_bytes: bytes, target_path: Path) -> None:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(image_bytes)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest fastaicode-image-mcp/tests/test_client.py -v`
Expected: PASS

### Task 4: Implement the MCP tool surface for generate_image

**Files:**
- Modify: `fastaicode-image-mcp/server/mcp_server.py`
- Test: `fastaicode-image-mcp/tests/test_mcp_tool.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from server.mcp_server import generate_image


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def generate(self, **kwargs):
        return self.payload


def test_generate_image_returns_saved_path(tmp_path, monkeypatch):
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
base_url = "http://new.fastaicode.top"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"

[size_preset_mapping]
1k = "1024x1024"
2k = "auto"
4k = "2048x2048"
auto = "auto"
        """.strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FASTAICODE_API_KEY", "secret")

    result = generate_image(
        prompt="a tiny red circle on a white background",
        size_preset="1k",
        output_path=str(tmp_path / "custom" / "circle.png"),
        filename_hint=None,
        model=None,
        config_file=config_file,
        client=FakeClient(
            {
                "created": 1776860842,
                "data": [{"b64_json": "cG5nLWJ5dGVz", "revised_prompt": "clean prompt"}],
            }
        ),
        now_text="20260423-153000",
    )

    assert result["ok"] is True
    assert result["saved_path"].endswith("circle.png")
    assert Path(result["saved_path"]).read_bytes() == b"png-bytes"
    assert result["resolved_request_size"] == "1024x1024"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest fastaicode-image-mcp/tests/test_mcp_tool.py -v`
Expected: FAIL because `generate_image` does not exist yet.

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path
from datetime import datetime

from server.client import decode_and_save_png, parse_generation_payload
from server.config import load_settings, resolve_size_preset
from server.naming import build_output_path


def generate_image(
    prompt: str,
    size_preset: str = "auto",
    output_path: str | None = None,
    filename_hint: str | None = None,
    model: str | None = None,
    config_file: Path | None = None,
    client=None,
    now_text: str | None = None,
) -> dict:
    settings = load_settings(config_file or Path("fastaicode-image-mcp.toml"))
    resolved_size = resolve_size_preset(size_preset, settings.size_preset_mapping)
    request_model = model or settings.default_model
    payload = client.generate(
        base_url=settings.base_url,
        api_key=settings.api_key,
        model=request_model,
        prompt=prompt,
        response_format="b64_json",
        size=resolved_size,
        timeout_seconds=settings.request_timeout_seconds,
    )
    parsed = parse_generation_payload(payload)
    stamp = now_text or datetime.now().strftime("%Y%m%d-%H%M%S")
    target = Path(output_path) if output_path else build_output_path(
        settings.default_output_dir, prompt, filename_hint, stamp
    )
    decode_and_save_png(parsed.image_bytes, target)
    return {
        "ok": True,
        "saved_path": str(target),
        "filename": target.name,
        "model": request_model,
        "size_preset": size_preset,
        "resolved_request_size": resolved_size,
        "created": parsed.created,
        "revised_prompt": parsed.revised_prompt,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest fastaicode-image-mcp/tests/test_mcp_tool.py -v`
Expected: PASS

### Task 5: Add real HTTP client, Skill docs, and final verification

**Files:**
- Modify: `fastaicode-image-mcp/server/client.py`
- Create: `fastaicode-image-mcp/skills/fastaicode-image/SKILL.md`
- Create: `fastaicode-image-mcp/fastaicode-image-mcp.toml`
- Modify: `CURRENT_TASK.md`
- Test: `fastaicode-image-mcp/tests/test_client.py`

- [ ] **Step 1: Write the failing HTTP client test**

```python
from unittest.mock import Mock

import httpx

from server.client import FastAIImageClient


def test_http_client_posts_expected_payload():
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"created": 1, "data": [{"b64_json": "cG5nLWJ5dGVz"}]},
        )
    )
    client = FastAIImageClient(http_client=httpx.Client(transport=transport))

    payload = client.generate(
        base_url="http://new.fastaicode.top",
        api_key="secret",
        model="gpt-image-2",
        prompt="red circle",
        response_format="b64_json",
        size="1024x1024",
        timeout_seconds=30,
    )

    assert payload["created"] == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest fastaicode-image-mcp/tests/test_client.py -v`
Expected: FAIL because `FastAIImageClient` is not implemented.

- [ ] **Step 3: Write minimal implementation**

```python
import httpx


class FastAIImageClient:
    def __init__(self, http_client: httpx.Client | None = None) -> None:
        self._http_client = http_client or httpx.Client()

    def generate(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
        response_format: str,
        size: str | None,
        timeout_seconds: float,
    ) -> dict:
        body = {
            "model": model,
            "prompt": prompt,
            "response_format": response_format,
        }
        if size and size != "auto":
            body["size"] = size
        response = self._http_client.post(
            f"{base_url.rstrip('/')}/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
```

- [ ] **Step 4: Write the Skill and example config**

```md
# fastaicode-image

Use this skill when the user wants to generate an image through the FastAICode-compatible image API.

Rules:
- Prefer the MCP tool `generate_image`
- Default `size_preset` to `auto` unless the user explicitly asks for `1k`, `2k`, or `4k`
- Let the tool save to `outputs/images/` unless the user specifies `output_path`
- If the tool returns `ok: false`, surface `error_code`, `message`, and `details`
```

```toml
base_url = "http://new.fastaicode.top"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"
request_timeout_seconds = 60

[size_preset_mapping]
1k = "1024x1024"
2k = "auto"
4k = "2048x2048"
auto = "auto"
```

- [ ] **Step 5: Run the focused suite**

Run: `pytest fastaicode-image-mcp/tests -v`
Expected: PASS

- [ ] **Step 6: Run one local smoke command**

Run: `python fastaicode-image-mcp/server/mcp_server.py`
Expected: server starts without import errors or prints a clear startup message.

- [ ] **Step 7: Update task status**

Write back:
- `CURRENT_TASK.md` status updated to implemented
- verification results recorded
- next step set to real API smoke test when credentials are available
