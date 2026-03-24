"""Tests for scraper.utils (domain + industries normalization)."""

from __future__ import annotations

import json

import pytest

from scraper.utils import normalize_industries_json, parse_company_domain


@pytest.mark.parametrize(
    ("website", "expected"),
    [
        ("https://www.foo.com/path", "www.foo.com"),
        ("example.com", "example.com"),
        ("", None),
        (None, None),
    ],
)
def test_parse_company_domain(website: str | None, expected: str | None) -> None:
    assert parse_company_domain(website) == expected


@pytest.mark.parametrize(
    ("value", "expected_json"),
    [
        (["fintech", "b2b"], '["fintech","b2b"]'),
        ([{"name": "B2B"}, {"slug": "x", "name": "SaaS"}], '["B2B","SaaS"]'),
        ([], "[]"),
        (None, "[]"),
    ],
)
def test_normalize_industries_json(value, expected_json: str) -> None:
    out = normalize_industries_json(value)
    assert out == expected_json
    json.loads(out)
