from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.client import FastAIImageClient, decode_and_save_png, parse_generation_payload
from server.config import load_settings, resolve_size_preset
from server.naming import build_output_path

PLUGIN_NAME = "fastaicode-image-mcp"
PLUGIN_VERSION = "0.1.0"
DEFAULT_CONFIG_FILE = Path(__file__).resolve().parents[1] / "fastaicode-image-mcp.toml"
TOOL_SCHEMA = {
    "name": "generate_image",
    "description": "Generate an image through the FastAICode image API and save a PNG locally.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Image generation prompt."},
            "size_preset": {
                "type": "string",
                "enum": ["1k", "2k", "4k", "auto"],
                "description": "Logical size preset for generation.",
            },
            "output_path": {"type": "string", "description": "Optional explicit output file path."},
            "filename_hint": {"type": "string", "description": "Optional readable file name hint."},
            "model": {"type": "string", "description": "Optional model override."},
        },
        "required": ["prompt"],
    },
}
EDIT_TOOL_SCHEMA = {
    "name": "edit_image",
    "description": "Edit a local source image through the FastAICode image edits API and save a PNG locally.",
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Edit instruction prompt."},
            "input_image_path": {"type": "string", "description": "Path to the local source image."},
            "size_preset": {
                "type": "string",
                "enum": ["1k", "2k", "4k", "auto"],
                "description": "Logical size preset for editing.",
            },
            "output_path": {"type": "string", "description": "Optional explicit output file path."},
            "filename_hint": {"type": "string", "description": "Optional readable file name hint."},
            "model": {"type": "string", "description": "Optional model override."},
        },
        "required": ["prompt", "input_image_path"],
    },
}


def generate_image(
    *,
    prompt: str,
    size_preset: str = "auto",
    output_path: str | None = None,
    filename_hint: str | None = None,
    model: str | None = None,
    config_file: Path | None = None,
    client=None,
    now_text: str | None = None,
) -> dict:
    settings = load_settings(config_file or DEFAULT_CONFIG_FILE)
    if client is None:
        client = FastAIImageClient()

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
    target_path = (
        Path(output_path)
        if output_path
        else build_output_path(settings.default_output_dir, prompt, filename_hint, stamp)
    )
    decode_and_save_png(parsed.image_bytes, target_path)
    return {
        "ok": True,
        "saved_path": str(target_path),
        "filename": target_path.name,
        "model": request_model,
        "size_preset": size_preset,
        "resolved_request_size": resolved_size,
        "created": parsed.created,
        "revised_prompt": parsed.revised_prompt,
    }


def edit_image(
    *,
    prompt: str,
    input_image_path: str,
    size_preset: str = "auto",
    output_path: str | None = None,
    filename_hint: str | None = None,
    model: str | None = None,
    config_file: Path | None = None,
    client=None,
    now_text: str | None = None,
) -> dict:
    settings = load_settings(config_file or DEFAULT_CONFIG_FILE)
    if client is None:
        client = FastAIImageClient()

    source_path = Path(input_image_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Input image not found: {input_image_path}")
    if not source_path.is_file():
        raise FileNotFoundError(f"Input image is not a file: {input_image_path}")

    resolved_size = resolve_size_preset(size_preset, settings.size_preset_mapping)
    request_model = model or settings.default_model
    payload = client.edit(
        base_url=settings.base_url,
        api_key=settings.api_key,
        model=request_model,
        prompt=prompt,
        image_path=source_path,
        size=resolved_size,
        timeout_seconds=settings.request_timeout_seconds,
    )
    parsed = parse_generation_payload(payload)
    stamp = now_text or datetime.now().strftime("%Y%m%d-%H%M%S")
    target_path = (
        Path(output_path)
        if output_path
        else build_output_path(settings.default_output_dir, prompt, filename_hint, stamp)
    )
    decode_and_save_png(parsed.image_bytes, target_path)
    return {
        "ok": True,
        "saved_path": str(target_path),
        "filename": target_path.name,
        "model": request_model,
        "size_preset": size_preset,
        "resolved_request_size": resolved_size,
        "source_image_path": str(source_path),
        "created": parsed.created,
        "revised_prompt": parsed.revised_prompt,
    }


def handle_message(
    message: dict,
    *,
    config_file: Path | None = None,
    client=None,
    now_text: str | None = None,
) -> dict | None:
    method = message.get("method")
    request_id = message.get("id")

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {},
        }

    if method == "initialize":
        params = message.get("params", {})
        protocol_version = params.get("protocolVersion", "2025-06-18")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol_version,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": PLUGIN_NAME, "version": PLUGIN_VERSION},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": [TOOL_SCHEMA, EDIT_TOOL_SCHEMA]},
        }

    if method == "tools/call":
        params = message.get("params", {})
        tool_name = params.get("name")
        if tool_name not in {"generate_image", "edit_image"}:
            return _jsonrpc_error(request_id, -32602, f"Unknown tool: {tool_name}")
        arguments = params.get("arguments", {})
        try:
            if tool_name == "generate_image":
                result = generate_image(
                    prompt=arguments["prompt"],
                    size_preset=arguments.get("size_preset", "auto"),
                    output_path=arguments.get("output_path"),
                    filename_hint=arguments.get("filename_hint"),
                    model=arguments.get("model"),
                    config_file=config_file,
                    client=client,
                    now_text=now_text,
                )
            else:
                result = edit_image(
                    prompt=arguments["prompt"],
                    input_image_path=arguments["input_image_path"],
                    size_preset=arguments.get("size_preset", "auto"),
                    output_path=arguments.get("output_path"),
                    filename_hint=arguments.get("filename_hint"),
                    model=arguments.get("model"),
                    config_file=config_file,
                    client=client,
                    now_text=now_text,
                )
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=True)}],
                    "isError": False,
                    "structuredContent": result,
                },
            }
        except Exception as exc:
            error_result = {
                "ok": False,
                "error_code": type(exc).__name__,
                "message": str(exc),
                "details": {},
            }
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": json.dumps(error_result, ensure_ascii=True)}],
                    "isError": True,
                    "structuredContent": error_result,
                },
            }

    return _jsonrpc_error(request_id, -32601, f"Method not found: {method}")


def _jsonrpc_error(request_id: object, code: int, message: str) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _read_message(stream=None) -> dict | None:
    stream = stream or sys.stdin.buffer
    first_line = stream.readline()
    if not first_line:
        return None

    if first_line in (b"\r\n", b"\n"):
        return _read_message(stream)

    if first_line.lower().startswith(b"content-length:"):
        headers: dict[str, str] = {}
        line = first_line
        while True:
            if line in (b"\r\n", b"\n"):
                break
            key, _, value = line.decode("utf-8").partition(":")
            headers[key.strip().lower()] = value.strip()
            line = stream.readline()
            if not line:
                return None

        length_text = headers.get("content-length")
        if not length_text:
            raise ValueError("Missing Content-Length header")
        content_length = int(length_text)
        body = stream.read(content_length)
        if not body:
            return None
        return json.loads(body.decode("utf-8"))

    return json.loads(first_line.decode("utf-8").strip())


def _write_message(message: dict, stream=None) -> None:
    stream = stream or sys.stdout.buffer
    body = json.dumps(message, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    stream.write(body)
    stream.write(b"\n")
    stream.flush()


def main() -> None:
    while True:
        message = _read_message()
        if message is None:
            return
        response = handle_message(message)
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    main()
