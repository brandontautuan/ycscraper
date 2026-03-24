"""Paginated YC companies API client → SQLite `companies` table."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx

from scraper.models import init_db, upsert_company
from scraper.utils import fetch_json, normalize_industries_json, parse_company_domain

logger = logging.getLogger(__name__)

CONFIRMED_ENDPOINT_MARKER = "api.ycombinator.com/v0.1/companies"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def ensure_api_recon_documents_endpoint() -> None:
    """Halt if docs/API_RECON.md does not contain the confirmed listing API (per Phase 2 plan)."""
    recon = _repo_root() / "docs" / "API_RECON.md"
    if not recon.is_file():
        print(
            "ERROR: docs/API_RECON.md is missing. Document the confirmed companies API before scraping.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    text = recon.read_text(encoding="utf-8")
    if CONFIRMED_ENDPOINT_MARKER not in text:
        print(
            "ERROR: docs/API_RECON.md has no confirmed companies endpoint "
            f"(expected '{CONFIRMED_ENDPOINT_MARKER}' in the endpoint log). "
            "Fill the table in API_RECON before running scrape.",
            file=sys.stderr,
        )
        raise SystemExit(2)


def build_companies_page_url(base: str, page: int, per_page: int) -> str:
    """Merge page/per_page into the companies API URL query string."""
    p = urlparse(base.strip())
    q = dict(parse_qsl(p.query, keep_blank_values=True))
    q["page"] = str(page)
    q["per_page"] = str(per_page)
    new_query = urlencode(sorted(q.items()))
    return urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))


def map_company_row(raw: dict[str, Any], scraped_at: str) -> dict[str, Any] | None:
    """Map API JSON object to DB row; return None if unusable."""
    cid = raw.get("id")
    if cid is None:
        logger.warning("skip company object without id: %s", raw.get("name"))
        return None
    name = (raw.get("name") or "").strip()
    slug = (raw.get("slug") or "").strip() or str(int(cid))
    website = raw.get("website")
    website_str = website.strip() if isinstance(website, str) else ""
    long_desc = raw.get("longDescription")
    if long_desc is None:
        desc = ""
    elif isinstance(long_desc, str):
        desc = long_desc
    else:
        desc = str(long_desc)
    one = raw.get("oneLiner")
    one_liner = one if isinstance(one, str) else ("" if one is None else str(one))
    return {
        "yc_company_id": int(cid),
        "name": name or slug,
        "slug": slug,
        "yc_batch": raw.get("batch"),
        "website": website_str or None,
        "yc_profile_url": raw.get("url") if isinstance(raw.get("url"), str) else None,
        "one_liner": one_liner or None,
        "description": desc,
        "industries_json": normalize_industries_json(raw.get("industries")),
        "company_domain": parse_company_domain(website_str or None),
        "scraped_at": scraped_at,
        "data_source": "yc_api",
    }


def run_company_scrape(
    *,
    db_path: str,
    request_delay: float,
    api_url: str,
    per_page: int,
    max_pages: int | None = None,
    max_companies: int | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Fetch all pages (within limits), upsert companies. Returns simple counters.
    """
    ensure_api_recon_documents_endpoint()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
    )
    scraped_at = datetime.now(timezone.utc).isoformat()
    headers = {
        "User-Agent": "ycscraper/0.1 (+https://github.com/brandontautuan/ycscraper; research)",
        "Accept": "application/json",
    }
    pages_done = 0
    companies_written = 0
    fetch_errors = 0
    next_url: str | None = build_companies_page_url(api_url, 1, per_page)
    conn = init_db(db_path) if not dry_run else None
    try:
        with httpx.Client(headers=headers) as client:
            while next_url:
                if max_pages is not None and pages_done >= max_pages:
                    logger.info("Stopping: reached max_pages=%s", max_pages)
                    break
                try:
                    data = fetch_json(
                        client,
                        next_url,
                        request_delay=request_delay,
                    )
                except Exception as e:
                    fetch_errors += 1
                    logger.error("Fetch failed: %s", e)
                    break
                pages_done += 1
                companies = data.get("companies")
                if not isinstance(companies, list):
                    logger.error("Unexpected payload: 'companies' not a list")
                    fetch_errors += 1
                    break
                for raw in companies:
                    if not isinstance(raw, dict):
                        continue
                    if max_companies is not None and companies_written >= max_companies:
                        next_url = None
                        break
                    row = map_company_row(raw, scraped_at)
                    if row is None:
                        continue
                    if dry_run:
                        companies_written += 1
                        continue
                    assert conn is not None
                    upsert_company(conn, row)
                    companies_written += 1
                if conn is not None:
                    conn.commit()
                if dry_run:
                    logger.info("Dry run: fetched one page only, no DB writes.")
                    break
                if next_url is None:
                    break
                nxt = data.get("nextPage")
                if isinstance(nxt, str) and nxt.strip():
                    next_url = nxt.strip()
                else:
                    page = int(data.get("page") or 1)
                    total_pages = int(data.get("totalPages") or page)
                    if page >= total_pages:
                        next_url = None
                    else:
                        next_url = build_companies_page_url(api_url, page + 1, per_page)
    finally:
        if conn is not None:
            conn.close()
    logger.info(
        "Done: pages=%s companies=%s fetch_errors=%s dry_run=%s",
        pages_done,
        companies_written,
        fetch_errors,
        dry_run,
    )
    return {
        "pages": pages_done,
        "companies": companies_written,
        "fetch_errors": fetch_errors,
    }

