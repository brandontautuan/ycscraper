# YC Founder Scraper — Project Context & Phases

## Project Overview

A web scraper that targets the Y Combinator public company directory to extract structured data about YC-backed companies and their founders. The goal is to build a pipeline that collects founder names, LinkedIn profiles, emails, and company details — and stores them in a queryable format for outreach, research, or analysis.

---

## Goals

- Scrape all publicly available YC company listings
- Extract founder names and their associated company data
- Collect company one-liners, full descriptions, and industry tags
- Collect LinkedIn profile URLs for each founder
- Enrich records with founder email addresses via third-party APIs
- Store everything in a clean, exportable format (CSV / SQLite)
- Run reliably at scale without getting blocked

---

## Tech Stack

| Layer | Tool |
|---|---|
| HTTP requests | `httpx` / `requests` |
| Browser automation | `Playwright` |
| HTML parsing | `BeautifulSoup4` |
| Data storage | `SQLite` + `pandas` |
| Email enrichment | Hunter.io / Apollo.io API |
| Rate limiting | `time.sleep` + retry logic |
| Environment config | `python-dotenv` |

---

## Data Schema

Each record should contain:

```
{
  company_name:        string,
  yc_batch:            string,     // e.g. "W24", "S23"
  company_url:         string,
  company_domain:      string,
  one_liner:           string,     // short tagline from API (e.g. "Stripe for X")
  description:         string,     // full paragraph description from company profile
  industries:          string[],   // industry tags (e.g. ["fintech", "b2b"])
  founder_name:        string,
  founder_linkedin:    string,
  founder_email:       string,
  email_confidence:    float,      // 0.0–1.0 score from Hunter/Apollo
  email_source:        string,     // "hunter" | "apollo" | "guessed"
  data_source:         string,     // "yc_api" | "scraped" | "enriched"
  scraped_at:          timestamp
}
```

> **Note on descriptions:** Both `one_liner` and `description` are expected to be present directly in the YC API response payload — no additional page visits are required to retrieve them. Industry tags are also typically included in the same response.

---

## Phases

---

### Phase 1 — Reconnaissance & API Discovery

**Goal:** Understand how YC's website loads data before writing a single scraper line.

**Tasks:**
- Open `ycombinator.com/companies` in Chrome DevTools (Network → Fetch/XHR tab)
- Identify the underlying API endpoint(s) being called (e.g. `api.ycombinator.com/v0.1/companies`)
- Document query parameters: `page`, `batch`, `industry`, `status`, etc.
- Check `robots.txt` at `ycombinator.com/robots.txt`
- Capture sample API responses and map out the JSON structure
- Determine if auth tokens or cookies are required

**Deliverables:**
- Documented API endpoint(s) with sample responses
- Notes on pagination strategy
- `robots.txt` compliance checklist

---

### Phase 2 — Company Data Scraper

**Goal:** Pull all company listings with their metadata including descriptions.

**Tasks:**
- Write a paginated API client that iterates through all YC batches
- Extract per-company: name, batch, website URL, YC profile URL
- Map `one_liner` and `description` fields directly from API response payload
- Extract `industries` array from API response (no extra requests needed)
- Parse company domain from website URL
- Implement rate limiting (1–2s delay between requests)
- Handle errors, retries, and edge cases (empty pages, rate limit responses)
- Save raw results to SQLite `companies` table

**Sample API response fields to capture:**
```json
{
  "name": "Acme Corp",
  "slug": "acme-corp",
  "one_liner": "AI-powered logistics for SMBs",
  "long_description": "Acme Corp builds software that helps small businesses...",
  "website": "https://acmecorp.com",
  "batch": "W24",
  "industries": ["logistics", "ai", "b2b"]
}
```

**Key Files:**
```
scraper/
  company_scraper.py     # Pagination + API client
  models.py              # SQLite schema
  utils.py               # Domain parsing, retry logic
```

**Deliverables:**
- Populated `companies` table with all YC companies including one-liners, descriptions, and industry tags
- Logs showing scrape progress and error rate

---

### Phase 3 — Founder Data Scraper

**Goal:** For each company, extract founder names and their YC profile links.

**Tasks:**
- Visit each company's YC profile page (or pull from API if available)
- Extract founder names, titles, and their individual YC profile URLs
- Follow founder profile links to extract any listed LinkedIn URLs
- Handle companies with multiple founders (one row per founder)
- Store results in `founders` table linked to `companies`

**Key Files:**
```
scraper/
  founder_scraper.py     # Per-company founder extraction
  profile_parser.py      # Parses individual founder pages
```

**Deliverables:**
- Populated `founders` table with names + LinkedIn URLs where available
- Coverage report: % of founders with LinkedIn found

---

### Phase 4 — Email Enrichment

**Goal:** Find email addresses for founders where not publicly listed.

**Tasks:**
- Integrate Hunter.io API (`/v2/email-finder`) using founder name + company domain
- Integrate Apollo.io as a fallback enrichment source
- Implement pattern-based guessing as last resort (`first@domain.com`, `f.last@domain.com`)
- Validate email format with regex
- Track confidence score from Hunter/Apollo
- Update `founders` table with `email` and `email_source` fields

**Key Files:**
```
enrichment/
  hunter_client.py       # Hunter.io API wrapper
  apollo_client.py       # Apollo.io API wrapper
  email_guesser.py       # Pattern-based fallback
  enrichment_runner.py   # Orchestrates enrichment pipeline
```

**Deliverables:**
- Enriched `founders` table with emails + confidence scores
- Coverage report: % of founders with email found

---

### Phase 5 — Data Export & Cleanup

**Goal:** Produce clean, usable output files for downstream use.

**Tasks:**
- Deduplicate records (same founder across batches)
- Filter out incomplete records based on configurable thresholds
- Export to CSV with all fields
- Export a "high confidence" subset (has both LinkedIn + email)
- Add a simple CLI interface to trigger scrape, enrichment, and export

**Key Files:**
```
export/
  exporter.py            # CSV + filtered export logic
cli.py                   # Command-line interface
```

**Deliverables:**
- `founders_full.csv` — all records including descriptions and industry tags
- `founders_enriched.csv` — only records with LinkedIn + email
- Working CLI (`python cli.py scrape`, `python cli.py enrich`, `python cli.py export`)

---

### Phase 6 — Hardening & Scale

**Goal:** Make the scraper robust enough to run unattended and at full scale.

**Tasks:**
- Add proxy rotation support to avoid IP blocks
- Implement checkpointing so scrapes can resume after interruption
- Add a run scheduler (cron or APScheduler) for periodic re-scrapes
- Set up logging to file with rotation
- Write unit tests for parsers and enrichment clients
- Create a `README.md` with full setup and usage instructions

**Key Files:**
```
scraper/
  proxy_manager.py       # Rotating proxy support
  checkpoint.py          # Resume from last position
scheduler/
  runner.py              # Scheduled runs
tests/
  test_parsers.py
  test_enrichment.py
```

**Deliverables:**
- Fully resumable, scheduled scraper
- Test suite with >80% coverage on core modules
- Complete README

---

## Folder Structure (Final)

```
yc-scraper/
├── scraper/
│   ├── company_scraper.py
│   ├── founder_scraper.py
│   ├── profile_parser.py
│   ├── proxy_manager.py
│   ├── checkpoint.py
│   ├── models.py
│   └── utils.py
├── enrichment/
│   ├── hunter_client.py
│   ├── apollo_client.py
│   ├── email_guesser.py
│   └── enrichment_runner.py
├── export/
│   └── exporter.py
├── scheduler/
│   └── runner.py
├── tests/
│   ├── test_parsers.py
│   └── test_enrichment.py
├── cli.py
├── config.py
├── .env.example
├── requirements.txt
└── README.md
```

---

## Environment Variables

```env
HUNTER_API_KEY=your_hunter_key
APOLLO_API_KEY=your_apollo_key
PROXY_LIST=proxy1:port,proxy2:port    # optional
REQUEST_DELAY=1.5                      # seconds between requests
DB_PATH=data/yc_founders.db
```

---

## Legal & Ethical Notes

- Always check `robots.txt` before scraping
- Respect rate limits — do not hammer the server
- Email enrichment is for research/outreach only — comply with CAN-SPAM and GDPR
- Do not resell scraped data
- LinkedIn scraping directly violates their ToS — use their data only if surfaced via YC profiles