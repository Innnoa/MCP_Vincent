from server.config import load_settings, resolve_size_preset


def test_environment_base_url_overrides_file(tmp_path, monkeypatch) -> None:
    config_file = tmp_path / "config.toml"
    config_file.write_text(
        """
base_url = "http://from-file.example"
default_model = "gpt-image-2"
default_output_dir = "outputs/images"

[size_preset_mapping]
one_k = "1024x1024"
two_k = "auto"
auto = "auto"
        """.strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("FASTAICODE_BASE_URL", "http://from-env.example")
    monkeypatch.setenv("FASTAICODE_API_KEY", "secret")

    settings = load_settings(config_file)

    assert settings.base_url == "http://from-env.example"
    assert settings.size_preset_mapping["1k"] == "1024x1024"


def test_resolve_four_k_requires_explicit_mapping() -> None:
    mapping = {
        "1k": "1024x1024",
        "2k": "auto",
        "auto": "auto",
    }

    try:
        resolve_size_preset("4k", mapping)
    except ValueError as exc:
        assert "4k" in str(exc)
    else:
        raise AssertionError("expected ValueError")
