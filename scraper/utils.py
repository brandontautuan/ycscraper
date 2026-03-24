"""Domain parsing, industries JSON normalization, HTTP fetch with retries."""

from __future__ import annotations

import json
import logging
import random
import time
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)


def parse_company_domain(website: str | None) -> str | None:
    """
    Extract registrable-style host from a company website URL.
    None -> None; empty string -> None; missing scheme -> https assumed.
    """
    if website is None:
        return None
    if not isinstance(website, str):
        return None
    raw = website.strip()
    if not raw:
        return None
    if "://" not in raw:
        raw = f"https://{raw}"
    try:
        parsed = urlparse(raw)
    except ValueError:
        return None
    host = (parsed.hostname or "").strip().lower()
    return host or None


def normalize_industries_json(value: Any) -> str:
    """
    Normalize API `industries` to canonical JSON text: array of strings, e.g. '["a","b"]'.
    Accepts list[str], list[object] (uses `name` or str(item)), empty list, None.
    """
    if value is None:
        return "[]"
    if not isinstance(value, list):
        return "[]"
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            s = item.strip()
            if s:
                out.append(s)
        elif isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str) and name.strip():
                out.append(name.strip())
            else:
                out.append(json.dumps(item, sort_keys=True))
        else:
            out.append(str(item))
    return json.dumps(out, ensure_ascii=False, separators=(",", ":"))


def fetch_json(
    client: httpx.Client,
    url: str,
    *,
    request_delay: float,
    max_retries: int = 4,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    GET url, return parsed JSON. Sleeps request_delay before each attempt after the first.
    Retries on 429, 5xx, and transient transport errors with bounded exponential backoff.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries):
        if attempt > 0:
            sleep_s = min(8.0, (2**attempt) * 0.5) + random.uniform(0, 0.25)
            time.sleep(sleep_s)
        else:
            time.sleep(request_delay)
        try:
            resp = client.get(url, timeout=timeout)
        except httpx.RequestError as e:
            last_exc = e
            logger.warning("HTTP request error %s (attempt %s): %s", url, attempt + 1, e)
            continue
        if resp.status_code == 429 or resp.status_code >= 500:
            logger.warning(
                "HTTP %s for %s (attempt %s)", resp.status_code, url, attempt + 1
            )
            last_exc = RuntimeError(f"HTTP {resp.status_code}")
            continue
        resp.raise_for_status()
        return resp.json()
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Failed to fetch {url}")
