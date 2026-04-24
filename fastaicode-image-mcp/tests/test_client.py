import base64

import httpx

from server.client import (
    FastAIImageClient,
    build_request_timeout,
    decode_and_save_png,
    parse_generation_payload,
)


def test_parse_generation_payload_reads_b64_json() -> None:
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


def test_decode_and_save_png_writes_file(tmp_path) -> None:
    target = tmp_path / "image.png"

    decode_and_save_png(b"png-bytes", target)

    assert target.read_bytes() == b"png-bytes"


def test_http_client_posts_expected_payload() -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["accept"] = request.headers["Accept"]
        captured["user_agent"] = request.headers["User-Agent"]
        captured["body"] = request.read().decode("utf-8")
        return httpx.Response(
            200,
            json={"created": 1, "data": [{"b64_json": "cG5nLWJ5dGVz"}]},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = FastAIImageClient(http_client=http_client)

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
    assert captured["url"] == "http://new.fastaicode.top/v1/images/generations"
    assert captured["auth"] == "Bearer secret"
    assert captured["accept"] == "application/json"
    assert "Mozilla/5.0" in captured["user_agent"]
    assert '"size":"1024x1024"' in captured["body"]


def test_generate_uses_fine_grained_timeout_object() -> None:
    captured: dict = {}

    class FakeHTTPClient:
        def post(self, *args, **kwargs) -> httpx.Response:
            captured["timeout"] = kwargs["timeout"]
            return httpx.Response(
                200,
                request=httpx.Request("POST", args[0]),
                json={"created": 1, "data": [{"b64_json": "cG5nLWJ5dGVz"}]},
            )

    client = FastAIImageClient(http_client=FakeHTTPClient())

    client.generate(
        base_url="http://new.fastaicode.top",
        api_key="secret",
        model="gpt-image-2",
        prompt="red circle",
        response_format="b64_json",
        size="1024x1024",
        timeout_seconds=300,
    )

    timeout = captured["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.read == 300
    assert timeout.write == 60
    assert timeout.connect == 10
    assert timeout.pool == 10


def test_build_request_timeout_caps_non_read_timeouts() -> None:
    timeout = build_request_timeout(300)

    assert timeout.read == 300
    assert timeout.write == 60
    assert timeout.connect == 10
    assert timeout.pool == 10


def test_generate_surfaces_upstream_permission_message() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            403,
            request=request,
            json={
                "error": {
                    "message": "This group does not allow image generation",
                    "type": "permission_error",
                }
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = FastAIImageClient(http_client=http_client)

    try:
        client.generate(
            base_url="http://new.fastaicode.top",
            api_key="secret",
            model="gpt-image-2",
            prompt="red circle",
            response_format="b64_json",
            size="1024x1024",
            timeout_seconds=30,
        )
    except httpx.HTTPStatusError as exc:
        assert "This group does not allow image generation" in str(exc)
    else:
        raise AssertionError("expected HTTPStatusError")


def test_http_client_posts_multipart_edit_request(tmp_path) -> None:
    captured: dict = {}
    image_path = tmp_path / "input.png"
    image_path.write_bytes(b"fake-png")

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["Authorization"]
        captured["content_type"] = request.headers["Content-Type"]
        captured["accept"] = request.headers["Accept"]
        captured["user_agent"] = request.headers["User-Agent"]
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={"created": 2, "data": [{"b64_json": "cG5nLWJ5dGVz"}]},
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = FastAIImageClient(http_client=http_client)

    payload = client.edit(
        base_url="http://new.fastaicode.top",
        api_key="secret",
        model="gpt-image-2",
        prompt="turn this into a blue icon",
        image_path=image_path,
        size="1024x1024",
        timeout_seconds=30,
    )

    assert payload["created"] == 2
    assert captured["url"] == "http://new.fastaicode.top/v1/images/edits"
    assert captured["auth"] == "Bearer secret"
    assert captured["accept"] == "application/json"
    assert "Mozilla/5.0" in captured["user_agent"]
    assert "multipart/form-data" in captured["content_type"]
    assert b'turn this into a blue icon' in captured["body"]
    assert b'1024x1024' in captured["body"]
