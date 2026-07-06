from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_plugin_metadata_points_to_mcp_server() -> None:
    plugin_file = REPO_ROOT / ".codex-plugin" / "plugin.json"
    data = json.loads(plugin_file.read_text(encoding="utf-8"))

    assert data["name"] == "fastaicode-image-mcp"
    assert data["skills"] == "./skills/"
    assert data["mcpServers"] == "./.mcp.json"


def test_mcp_server_registration_is_portable() -> None:
    config_file = REPO_ROOT / ".mcp.json"
    data = json.loads(config_file.read_text(encoding="utf-8"))
    server = data["mcpServers"]["fastaicode-image"]

    assert server["command"] == "python3"
    assert server["args"] == ["./fastaicode-image-mcp/server/mcp_server.py"]


def test_mcp_server_registration_points_to_existing_script_from_workspace_root() -> None:
    workspace_root = REPO_ROOT.parent
    config_file = REPO_ROOT / ".mcp.json"
    data = json.loads(config_file.read_text(encoding="utf-8"))
    server = data["mcpServers"]["fastaicode-image"]
    script_path = workspace_root / server["args"][0]

    assert script_path.exists()
