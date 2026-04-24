from __future__ import annotations

import base64
from pathlib import Path
import json

import httpx

from server.models import ParsedImageResponse

DEFAULT_REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
    ),
}


def build_request_timeout(read_timeout_seconds: float) -> httpx.Timeout:
    bounded_timeout = max(float(read_timeout_seconds), 0.1)
    return httpx.Timeout(
        read=bounded_timeout,
        write=min(bounded_timeout, 60.0),
        connect=min(bounded_timeout, 10.0),
        pool=min(bounded_timeout, 10.0),
    )


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
                **DEFAULT_REQUEST_HEADERS,
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            content=json.dumps(body, separators=(",", ":")),
            timeout=build_request_timeout(timeout_seconds),
        )
        _raise_for_status_with_body(response)
        return response.json()

    def edit(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        prompt: str,
        image_path: Path,
        size: str | None,
        timeout_seconds: float,
    ) -> dict:
        with image_path.open("rb") as image_file:
            data = {
                "model": model,
                "prompt": prompt,
            }
            if size and size != "auto":
                data["size"] = size
            response = self._http_client.post(
                f"{base_url.rstrip('/')}/v1/images/edits",
                headers={
                    **DEFAULT_REQUEST_HEADERS,
                    "Authorization": f"Bearer {api_key}",
                },
                data=data,
                files={
                    "image": (image_path.name, image_file, "image/png"),
                },
                timeout=build_request_timeout(timeout_seconds),
            )
        _raise_for_status_with_body(response)
        return response.json()


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


def _raise_for_status_with_body(response: httpx.Response) -> None:
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = _extract_error_message(response)
        if detail:
            message = f"{exc}\nUpstream error: {detail}"
            raise httpx.HTTPStatusError(message, request=exc.request, response=exc.response) from exc
        raise


def _extract_error_message(response: httpx.Response) -> str | None:
    try:
        payload = response.json()
    except ValueError:
        return None

    error = payload.get("error")
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip()
    return None
