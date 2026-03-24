"""CLI entrypoint (stubs). Config is only imported inside main() so missing .env does not break `import cli`."""

from __future__ import annotations

import argparse


def main() -> None:
    from config import (
        DB_PATH,
        REQUEST_DELAY,
        YC_COMPANIES_API_URL,
        YC_COMPANIES_PER_PAGE,
        YC_SCRAPE_DRY_RUN,
        YC_SCRAPE_MAX_COMPANIES,
        YC_SCRAPE_MAX_PAGES,
    )

    parser = argparse.ArgumentParser(
        description="YC founder scraper CLI",
        epilog=f"Env defaults: REQUEST_DELAY={REQUEST_DELAY}, DB_PATH={DB_PATH!r}",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    scrape_p = sub.add_parser("scrape", help="Fetch YC companies into SQLite (Phase 2)")
    scrape_p.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Stop after N pages (overrides YC_SCRAPE_MAX_PAGES if set)",
    )
    scrape_p.add_argument(
        "--max-companies",
        type=int,
        default=None,
        help="Stop after N companies (overrides YC_SCRAPE_MAX_COMPANIES if set)",
    )
    scrape_p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch first page only, no DB writes (also see YC_SCRAPE_DRY_RUN)",
    )
    sub.add_parser("enrich", help="Run enrichment (not implemented)")
    sub.add_parser("export", help="Run export (not implemented)")
    args = parser.parse_args()
    if args.command == "scrape":
        from scraper.company_scraper import run_company_scrape

        max_pages = args.max_pages if args.max_pages is not None else YC_SCRAPE_MAX_PAGES
        max_companies = (
            args.max_companies
            if args.max_companies is not None
            else YC_SCRAPE_MAX_COMPANIES
        )
        dry_run = bool(args.dry_run or YC_SCRAPE_DRY_RUN)
        run_company_scrape(
            db_path=DB_PATH,
            request_delay=REQUEST_DELAY,
            api_url=YC_COMPANIES_API_URL,
            per_page=YC_COMPANIES_PER_PAGE,
            max_pages=max_pages,
            max_companies=max_companies,
            dry_run=dry_run,
        )
        return
    print(f"not implemented: {args.command}")


if __name__ == "__main__":
    main()
