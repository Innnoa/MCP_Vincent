from server.naming import build_output_path


def test_build_output_path_uses_timestamp_and_slug(tmp_path) -> None:
    path = build_output_path(
        output_root=tmp_path,
        prompt="a tiny red circle on a white background",
        filename_hint="red-circle",
        now_text="20260423-153000",
    )

    assert path.name == "20260423-153000-red-circle.png"
    assert path.parent == tmp_path
