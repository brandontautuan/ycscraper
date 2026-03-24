"""Load environment-driven settings. Safe to import without a populated .env."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

REQUEST_DELAY: float = float(os.getenv("REQUEST_DELAY", "1.5"))
DB_PATH: str = os.getenv("DB_PATH", "data/yc_founders.db")

# YC public companies listing API (must match docs/API_RECON.md endpoint log).
YC_COMPANIES_API_URL: str = os.getenv(
    "YC_COMPANIES_API_URL",
    "https://api.ycombinator.com/v0.1/companies",
)
YC_COMPANIES_PER_PAGE: int = max(1, int(os.getenv("YC_COMPANIES_PER_PAGE", "25")))

# Optional safety limits (empty / unset = no limit).
def _optional_int(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None
    return int(raw)


YC_SCRAPE_MAX_PAGES: int | None = _optional_int("YC_SCRAPE_MAX_PAGES")
YC_SCRAPE_MAX_COMPANIES: int | None = _optional_int("YC_SCRAPE_MAX_COMPANIES")
YC_SCRAPE_DRY_RUN: bool = os.getenv("YC_SCRAPE_DRY_RUN", "").strip().lower() in (
    "1",
    "true",
    "yes",
)
