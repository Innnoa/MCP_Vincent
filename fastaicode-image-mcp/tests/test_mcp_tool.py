from io import BytesIO
from pathlib import Path

from server.mcp_server import _read_message, _write_message, edit_image, generate_image, handle_message


class FakeClient:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[dict] = []

    def generate(self, **kwargs) -> dict:
        self.calls.append(kwargs)
        return self.payload


def test_generate_image_returns_saved_path(tmp_path, monkeypatch) -> None:
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
    fake_client = FakeClient(
        {
            "created": 1776860842,
            "data": [
                {
                    "b64_json": "cG5nLWJ5dGVz",
                    "revised_prompt": "clean prompt",
                }
            ],
        }
    )

    result = generate_image(
        prompt="a tiny red circle on a white background",
        size_preset="1k",
        output_path=str(tmp_path / "custom" / "circle.png"),
        filename_hint=None,
        model=None,
        config_file=config_file,
        client=fake_client,
        now_text="20260423-153000",
    )

    assert result["ok"] is True
    assert result["saved_path"].endswith("circle.png")
    assert Path(result["saved_path"]).read_bytes() == b"png-bytes"
    assert result["resolved_request_size"] == "1024x1024"
    assert fake_client.calls[0]["model"] == "gpt-image-2"


def test_initialize_returns_tools_capability() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "tester", "version": "1.0.0"},
            },
        }
    )

    assert response["id"] == 1
    assert response["result"]["protocolVersion"] == "2025-06-18"
    assert response["result"]["capabilities"]["tools"]["listChanged"] is False
    assert response["result"]["serverInfo"]["name"] == "fastaicode-image-mcp"


def test_tools_list_exposes_generate_image() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
    )

    tool = response["result"]["tools"][0]
    assert tool["name"] == "generate_image"
    assert "prompt" in tool["inputSchema"]["properties"]
    assert tool["inputSchema"]["required"] == ["prompt"]
    tool_names = [item["name"] for item in response["result"]["tools"]]
    assert "edit_image" in tool_names


def test_ping_returns_empty_result() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 20,
            "method": "ping",
            "params": {},
        }
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 20,
        "result": {},
    }


def test_read_message_accepts_newline_delimited_jsonrpc() -> None:
    stream = BytesIO(b'{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}\n')

    message = _read_message(stream)

    assert message == {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "ping",
        "params": {},
    }


def test_read_message_keeps_legacy_content_length_support() -> None:
    body = b'{"jsonrpc":"2.0","id":2,"method":"ping","params":{}}'
    stream = BytesIO(f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8") + body)

    message = _read_message(stream)

    assert message == {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "ping",
        "params": {},
    }


def test_write_message_emits_newline_delimited_jsonrpc() -> None:
    stream = BytesIO()

    _write_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "result": {},
        },
        stream,
    )

    assert stream.getvalue() == b'{"jsonrpc":"2.0","id":3,"result":{}}\n'


def test_tools_call_wraps_successful_tool_result(tmp_path, monkeypatch) -> None:
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

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "generate_image",
                "arguments": {
                    "prompt": "red circle",
                    "size_preset": "1k",
                    "output_path": str(tmp_path / "image.png"),
                },
            },
        },
        config_file=config_file,
        client=FakeClient(
            {
                "created": 1776860842,
                "data": [{"b64_json": "cG5nLWJ5dGVz"}],
            }
        ),
        now_text="20260423-153000",
    )

    assert response["result"]["isError"] is False
    assert response["result"]["structuredContent"]["ok"] is True
    assert response["result"]["structuredContent"]["saved_path"].endswith("image.png")


def test_tools_call_wraps_structured_error_when_api_key_missing(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
base_url = "http://new.fastaicode.top"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"

[size_preset_mapping]
1k = "1024x1024"
auto = "auto"
        """.strip(),
        encoding="utf-8",
    )
    monkeypatch.delenv("FASTAICODE_API_KEY", raising=False)

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "generate_image",
                "arguments": {"prompt": "red circle"},
            },
        },
        config_file=config_file,
        client=FakeClient({"data": [{"b64_json": "cG5n"}]}),
    )

    assert response["result"]["isError"] is True
    assert response["result"]["structuredContent"]["ok"] is False
    assert response["result"]["structuredContent"]["error_code"] == "ValueError"


def test_edit_image_returns_saved_path(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
base_url = "http://new.fastaicode.top"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"

[size_preset_mapping]
1k = "1024x1024"
auto = "auto"
        """.strip(),
        encoding="utf-8",
    )
    input_image = tmp_path / "input.png"
    input_image.write_bytes(b"source-image")
    monkeypatch.setenv("FASTAICODE_API_KEY", "secret")
    fake_client = FakeClient(
        {
            "created": 1776909000,
            "data": [
                {
                    "b64_json": "cG5nLWJ5dGVz",
                    "revised_prompt": "blue icon style",
                }
            ],
        }
    )
    fake_client.edit = fake_client.generate

    result = edit_image(
        prompt="turn this into a blue icon",
        input_image_path=str(input_image),
        size_preset="1k",
        output_path=str(tmp_path / "edited" / "blue-icon.png"),
        filename_hint=None,
        model=None,
        config_file=config_file,
        client=fake_client,
        now_text="20260423-160000",
    )

    assert result["ok"] is True
    assert result["saved_path"].endswith("blue-icon.png")
    assert result["source_image_path"] == str(input_image)
    assert Path(result["saved_path"]).read_bytes() == b"png-bytes"
    assert fake_client.calls[0]["size"] == "1024x1024"


def test_edit_image_returns_structured_error_when_source_missing(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
base_url = "http://new.fastaicode.top"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"

[size_preset_mapping]
1k = "1024x1024"
auto = "auto"
        """.strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FASTAICODE_API_KEY", "secret")

    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "edit_image",
                "arguments": {
                    "prompt": "turn this into a blue icon",
                    "input_image_path": str(tmp_path / "missing.png"),
                },
            },
        },
        config_file=config_file,
        client=FakeClient({"data": [{"b64_json": "cG5n"}]}),
    )

    assert response["result"]["isError"] is True
    assert response["result"]["structuredContent"]["ok"] is False
    assert response["result"]["structuredContent"]["error_code"] == "FileNotFoundError"
