# Phase 1 — API reconnaissance & discovery

This document tracks how the Y Combinator company directory loads data in the browser, what to verify in DevTools, and how that maps to the project schema in `master.md`. **No high-volume scraping** until endpoints, pagination, and `robots.txt` compliance are filled in here.

---

## Goals

- Identify **XHR/Fetch** calls made when loading `ycombinator.com/companies` (or equivalent listing UI).
- Record **candidate base URLs**, query parameters, and pagination behavior.
- Note **authentication** (cookies, headers, tokens) if any.
- Align discovered JSON fields with the **Phase 2+ pipeline** and the **Data Schema** in `master.md`.

---

## Steps (human — Chrome DevTools)

1. Open the YC companies experience in Chrome (e.g. directory or batch listing as you will scrape).
2. Open **DevTools → Network**, filter by **Fetch/XHR** (and **Doc** if the first load is server-driven).
3. Reload or paginate/filter and watch new requests.
4. For each relevant request, capture:
   - Full URL (origin + path)
   - HTTP method
   - Query string keys (e.g. `page`, `batch`, `industry`, `status`, … — **verify real names**)
   - Request headers that look required (e.g. `Cookie`, `Authorization`, custom headers)
5. Save **one sample JSON response** per important endpoint (see [How to paste samples](#how-to-paste-samples)).

---

## Query parameters to verify

Confirm which exist on the real API and what they mean (names may differ):

| Parameter (hypothesis) | Purpose to verify |
|------------------------|-------------------|
| `page` / `cursor` / offset | Pagination style (page number vs cursor vs infinite scroll token) |
| `batch` | Filter by YC batch (e.g. W24, S23) |
| `industry` / `industries` | Industry filter(s) |
| `status` | e.g. active / public / other filters |

Add any additional parameters you observe (e.g. search, sort).

---

## Pagination & rate limiting (notes)

- Document whether listing is **page-based**, **cursor-based**, or **infinite scroll** (next URL from response body).
- Note **total count** or **has_more**-style fields if present.
- **Intent:** polite delays (see `REQUEST_DELAY` in `.env.example`); no tight retry loops during recon.

---

## Auth / cookies

- [x] Requests work **without** login in your test session (verified `GET` on listing URL returns **200** with JSON; no `Cookie` / `Authorization` required as of 2026-03)  
- [ ] Or **session cookies** / headers are required — list which  
- [ ] Or **API tokens** appear — document header name and where they originate (do not commit values)

---

## Endpoint log (fill from DevTools)

| Endpoint (path or full URL pattern) | Method | Sample response path / notes |
|--------------------------------------|--------|------------------------------|
| `https://api.ycombinator.com/v0.1/companies` | GET | Query: `page` (1-based), `per_page`. Body: `{ "companies": [ {...} ], "nextPage": "<full URL or null>", "page": <int>, "totalPages": <int> }`. Sample company keys include `id`, `name`, `slug`, `website`, `oneLiner`, `longDescription`, `url` (YC profile), `batch`, `industries` (string array). Redacted fragment: see network capture or hit URL once in DevTools. |
| | | |

_Add rows as you discover calls. Prefer stable path patterns over one-off signed URLs._

### Pagination (confirmed)

- **Style:** page index + `totalPages`, with optional **`nextPage`** absolute URL for the following page.
- **Strategy in code:** prefer following **`nextPage`** when present; otherwise increment `page` until `page >= totalPages`.

---

## Schema mapping (`master.md` vs API)

Target record shape (from `master.md`):

| Our field | Expected source | Notes |
|-----------|-----------------|-------|
| `company_name` | API `name` | Stored as column `name` in SQLite `companies`. |
| `yc_batch` | API `batch` | e.g. `W24`, `P26`. |
| `company_url` / profile URL | API `url` | YC profile URL (`https://www.ycombinator.com/companies/...`). |
| `company_domain` | Derived from API `website` | Parsed in Phase 2 (`utils.parse_company_domain`). |
| `one_liner` | API `oneLiner` | CamelCase in JSON. |
| `description` | API `longDescription` | May be empty string; map to our long text field. |
| `industries` | API `industries` | **Array of strings** in live responses; normalize to JSON text `["..."]` in DB. |
| Founder / LinkedIn / email | Later phases | |

---

## Open gaps — confirm from real responses before Phase 2

**Resolved for `api.ycombinator.com/v0.1/companies` (verified 2026-03):**

1. **Short pitch:** JSON key is **`oneLiner`** → stored as `one_liner`.
2. **Long text:** JSON key is **`longDescription`** → stored as `description` (not `description` / `long_description` on this endpoint).
3. **`industries`:** **Array of strings** (e.g. `["B2B","Consumer"]`). Normalizer still accepts objects for forward-compatibility.

If YC changes the payload, update this section and `scraper/company_scraper.py` field mapping.

---

## `robots.txt` compliance checklist

- [ ] Read the saved snapshot at `docs/robots-ycombinator.txt` (refreshed via `scripts/fetch_yc_robots.py`).
- [ ] Note **Disallow** rules for paths you intend to hit (`/companies`, API hosts, etc.).
- [x] **Phase 2 bulk ingest** uses **`https://api.ycombinator.com/v0.1/companies`** (see endpoint log), **not** HTML listing URLs under `www` with query strings (`Disallow: /companies?*` on the `www` snapshot).
- [ ] **Crawl-delay** or similar directives if present — respect in code.
- [ ] **Rate limiting:** use env-driven delays; **do not hammer** YC or related hosts.
- [ ] Re-fetch `robots.txt` periodically if deployment or policy changes are a concern.

---

## How to paste samples

1. Copy **response JSON** from DevTools (or save to a local file **outside the repo**).
2. Paste a **redacted** fragment into this doc or attach in a secure channel — **remove** cookies, tokens, and personal data.
3. Prefer **one representative company object** plus **pagination wrapper** if applicable.
4. Note the **exact request URL** (with query string) that produced the sample.

---

## References

- Project phases and folder layout: `master.md`
- Live policy text snapshot: `docs/robots-ycombinator.txt`
