"""Small standard-library HTTP helpers."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


USER_AGENT = "paperutils/0.1 (+https://example.invalid/paperutils)"


class FetchError(RuntimeError):
    """Raised when a remote source cannot be fetched or parsed."""


def get_json(url: str, params: dict[str, Any] | None = None, timeout: float = 4.0) -> Any:
    """GET a JSON endpoint using urllib."""

    data = get_text(url, params=params, timeout=timeout)
    try:
        return json.loads(data)
    except json.JSONDecodeError as exc:
        raise FetchError(f"invalid JSON from {url}") from exc


def get_text(url: str, params: dict[str, Any] | None = None, timeout: float = 4.0) -> str:
    """GET a text endpoint using urllib."""

    if params:
        query = urllib.parse.urlencode(params, doseq=True)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_error: BaseException | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt == 0:
                time.sleep(0.2)
    raise FetchError(str(last_error))
