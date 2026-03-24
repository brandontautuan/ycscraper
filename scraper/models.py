"""SQLite schema and upserts for Phase 2 `companies` table."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def init_db(db_path: str) -> sqlite3.Connection:
    """Create data/ if needed, open DB, ensure `companies` table exists."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS companies (
            yc_company_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            yc_batch TEXT,
            website TEXT,
            yc_profile_url TEXT,
            one_liner TEXT,
            description TEXT,
            industries_json TEXT NOT NULL DEFAULT '[]',
            company_domain TEXT,
            scraped_at TEXT NOT NULL,
            data_source TEXT NOT NULL DEFAULT 'yc_api'
        );
        """
    )
    conn.commit()
    return conn


def upsert_company(conn: sqlite3.Connection, row: dict[str, Any]) -> None:
    """Insert or replace company; on conflict refresh all fields including scraped_at (last-write-wins)."""
    conn.execute(
        """
        INSERT INTO companies (
            yc_company_id, name, slug, yc_batch, website, yc_profile_url,
            one_liner, description, industries_json, company_domain,
            scraped_at, data_source
        ) VALUES (
            :yc_company_id, :name, :slug, :yc_batch, :website, :yc_profile_url,
            :one_liner, :description, :industries_json, :company_domain,
            :scraped_at, :data_source
        )
        ON CONFLICT(yc_company_id) DO UPDATE SET
            name = excluded.name,
            slug = excluded.slug,
            yc_batch = excluded.yc_batch,
            website = excluded.website,
            yc_profile_url = excluded.yc_profile_url,
            one_liner = excluded.one_liner,
            description = excluded.description,
            industries_json = excluded.industries_json,
            company_domain = excluded.company_domain,
            scraped_at = excluded.scraped_at,
            data_source = excluded.data_source;
        """,
        row,
    )
