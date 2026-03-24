#!/usr/bin/env python3
"""
Fetch Y Combinator robots.txt and write the result to docs/robots-ycombinator.txt.

Always writes that single path: either the robots body on HTTP 200, or a labeled
error on non-200. No aggressive retries (one attempt per URL, polite timeout).
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs" / "robots-ycombinator.txt"
URLS = (
    "https://www.ycombinator.com/robots.txt",
    "https://ycombinator.com/robots.txt",
)
TIMEOUT = 30.0


def _write_output(text: str) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    errors: list[str] = []

    with httpx.Client(timeout=TIMEOUT, follow_redirects=True) as client:
        for url in URLS:
            try:
                r = client.get(url)
            except httpx.RequestError as e:
                errors.append(f"{url}: request error ({type(e).__name__}: {e})")
                continue
            if r.status_code == 200:
                _write_output(r.text)
                return 0
            errors.append(f"{url}: HTTP {r.status_code}")

    body_lines = [
        f"ERROR: Could not fetch robots.txt successfully at {ts} (UTC)",
        "",
        "Attempts:",
    ]
    body_lines.extend(f"  - {line}" for line in errors)
    body_lines.append("")
    _write_output("\n".join(body_lines))
    return 1


if __name__ == "__main__":
    sys.exit(main())
