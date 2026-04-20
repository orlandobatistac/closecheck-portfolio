# CloseCheck — AI Pre-Close File Validator

CloseCheck is an AI-powered tool that validates real estate transaction files before closing. It ingests closing packages in any common format — PDF, DOCX, images, XLSX, CSV, HTML, JSON, TXT, and ZIP archives — extracts key data from each file using Claude, and runs a structured rule engine — returning a clear **Pass / Warning / Fail** report that flags missing documents, value inconsistencies, and compliance gaps in seconds.

The product replaces 2–4 hours of manual file review with a 60-second AI audit. Upload a closing package, watch the scan complete, and receive an executive summary with a prioritized action plan and one-click email drafts for every conflict detected.

---

## Documentation

- **[README.md](README.md)** — Main overview (this file)
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — Development setup, code style, testing guidelines
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Detailed system design, data flows, module breakdown
- **[docs/PROJECT.md](docs/PROJECT.md)** — Feature spec + rule matrix
- **[docs/CLAUDE.md](docs/CLAUDE.md)** — Claude Code / Copilot interaction guidelines
- **[docs/CLAUDE_CODE_PROMPTS.md](docs/CLAUDE_CODE_PROMPTS.md)** — Step-by-step feature implementation guide

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend API | FastAPI (Python 3.11+) | Async, OpenAPI docs at `/docs` |
| LLM Processing | Claude API (`claude-sonnet-4-6`) | Document classification, field extraction, OCR, executive brief |
| File Parsing | PyMuPDF, python-docx, openpyxl, BeautifulSoup4, Pillow | PDF, DOCX, XLSX, HTML, CSV, TXT, JSON, images |
| OCR | Claude Vision API | Scanned PDFs and standalone image files |
| Archive Handling | stdlib `zipfile` | ZIP with recursive extraction (up to 5 levels deep) |
| PDF Reports | ReportLab | Generated PDF validation reports |
| Database | SQLite via SQLAlchemy | Jobs and audit trail |
| Frontend | React 18 + Vite + Tailwind CSS | SPA — Upload → Processing → Report |
| HTTP Client | Axios | Frontend ↔ Backend |
| Auth | API Key header (MVP) | `X-API-Key` header |
| Deployment | Docker Compose | Backend + frontend in containers |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND (React)                  │
│  Upload UI → Processing Tracker → Validation Report  │
└───────────────────────┬─────────────────────────────┘
                        │ REST (multipart + JSON)
┌───────────────────────▼─────────────────────────────┐
│                  BACKEND (FastAPI)                   │
│                                                      │
│  POST /api/v1/validate                               │
│          │                                           │
│          ▼                                           │
│   ┌──────────────────────────────────────────┐       │
│   │          Ingestion Pipeline              │       │
│   │  1. Save uploaded files                  │       │
│   │  2. Expand ZIPs (recursive, ZIP-Slip     │       │
│   │     safe, up to 5 levels deep)           │       │
│   │  3. Deduplicate by SHA-256               │       │
│   │  4. Detect file type (magic bytes)       │       │
│   │  5. Route to format extractor:           │       │
│   │     PDF  → native text or OCR (Vision)  │       │
│   │     DOCX → paragraphs + tables           │       │
│   │     Image → Claude Vision OCR            │       │
│   │     XLSX → per-sheet CSV text            │       │
│   │     HTML → stripped plain text           │       │
│   │     CSV / TXT / JSON → normalized text   │       │
│   │  6. Normalize to ParsedDocument schema   │       │
│   └───────────────────┬──────────────────────┘       │
│                       │                              │
│               Document Classifier (Claude API)       │
│                       │                              │
│               Field Extractor (Claude API)           │
│                       │                              │
│               Rule Engine (40 rules)                 │
│                + Consistency Checks                  │
│                       │                              │
│               Report Builder (Claude API)            │
│            (executive brief + action plan)           │
│                       │                              │
│  GET  /api/v1/results/{id} ◄─────────────────────── │
│  GET  /api/v1/report/{id}/pdf                        │
│  POST /api/v1/jobs/{id}/draft-email                  │
└──────────────────────────────────────────────────────┘
```

---

## Quick Start

```bash
git clone <your-repo-url>
cd closecheck

# Configure backend
cp backend/.env.example backend/.env
# Edit backend/.env and add your ANTHROPIC_API_KEY

# Configure frontend (optional for Docker — proxy handles routing)
cp frontend/.env.example frontend/.env

# Launch everything
docker-compose up --build

# Open http://localhost:5173
```

For local development without Docker:

```bash
# All-in-one (starts both backend + frontend guides)
make dev

# Or, run them separately in two terminals:
# Terminal 1:
make dev-backend              # http://localhost:8000

# Terminal 2:
make dev-frontend             # http://localhost:5173
```

See [Makefile](Makefile) for the full list of development commands.

---

## Demo Walkthrough

1. **Upload** — Drag and drop 1–20 files onto the upload zone. Supported formats: PDF, DOCX, XLSX, CSV, HTML, TXT, JSON, images (JPG/PNG/GIF/TIFF/BMP/WebP), and ZIP archives (contents extracted automatically). Use the sample files in `sample-docs/Martinez_test/` to see intentional mismatches.

2. **Processing** — Watch 5 animated steps as CloseCheck ingests, classifies, extracts fields, cross-references documents, and generates the executive brief.

3. **Triage Banner** — The report opens with a color-coded verdict: **Ready to close** (green), **Needs review** (amber), or **Blocked** (red), plus a 5-bullet executive summary.

4. **Conflict Cards** — Each detected mismatch shows the two conflicting values side-by-side (e.g., purchase price `$385,000` in the purchase agreement vs `$387,500` in the closing disclosure).

5. **Action Plan & Email Drafts** — A prioritized to-do list generated by Claude, with one-click email drafts (professional and urgent variants) for each conflict.

> **Sample mismatches in `Martinez_test/`:**
> - `PA-003`: Purchase price `$385,000` (PA) vs `$387,500` (closing disclosure) — FAIL
> - `PA-001`: `Carlos Martinez` (PA/title) vs `Carlos Martínez` (lender commitment) — FAIL
> - Missing: insurance binder, ID document → additional FAILs

---

## Supported File Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| PDF | `.pdf` | Native text extraction; automatic OCR via Claude Vision for scanned pages |
| Word | `.docx` | Paragraphs and tables |
| Spreadsheet | `.xlsx`, `.xls` | Each sheet rendered as CSV-like text |
| CSV / TSV | `.csv`, `.tsv` | Auto-detects delimiter and encoding |
| HTML | `.html`, `.htm`, `.xhtml` | Scripts and styles stripped |
| Plain text | `.txt`, `.md` | UTF-8 / Latin-1 / CP-1252 auto-detection |
| JSON | `.json` | Pretty-printed; large arrays sampled to first 10 items |
| Images | `.jpg`, `.png`, `.gif`, `.tiff`, `.bmp`, `.webp` | OCR via Claude Vision |
| ZIP archive | `.zip` | Recursively extracted up to 5 levels; ZIP-Slip protected |

Files with unrecognized types are skipped with a warning — the job continues with the remaining files. Duplicate files (by SHA-256) are deduplicated automatically.

---

## Validation Rules

40 rules across 7 document categories, each with severity `FAIL`, `WARNING`, or `INFO`.

| Category | Rules | Key Checks |
|----------|-------|-----------|
| Purchase Agreement (PA) | PA-001 – PA-007 | Name consistency, price match, closing date, signatures, contingencies |
| Title Commitment (TC) | TC-001 – TC-007 | Title present, legal description, effective date, open liens, judgments |
| Loan / Mortgage (LN) | LN-001 – LN-006 | Loan amount, borrower name, note + deed present, LTV ≤ 97% |
| Closing Disclosure (CD) | CD-001 – CD-006 | CD/HUD-1 present, cash to close, seller credits, closing costs ≤ 5% |
| Property (PR) | PR-001 – PR-005 | Tax status, survey, HOA dues, certificate of occupancy |
| Insurance (IN) | IN-001 – IN-005 | Binder present, coverage ≥ loan, mortgagee, flood, effective date |
| Compliance (IC) | IC-001 – IC-004 | ID docs, FIRPTA, wire instructions, power of attorney |

See `PROJECT.md` for the full rule matrix with field-level detail.

---

## API Reference

### `POST /api/v1/validate`
Submit a closing package for validation.

```
Content-Type: multipart/form-data
files:            1–20 files (max 25 MB each)
                  Supported: PDF, DOCX, XLSX, CSV, HTML, TXT, JSON,
                  images (JPG/PNG/GIF/TIFF/BMP/WebP), ZIP archives
transaction_type: "residential" | "commercial"  (default: residential)
```

Response `202 Accepted`:
```json
{ "job_id": "uuid", "status": "pending", "created_at": "..." }
```

### `GET /api/v1/results/{job_id}`
Poll job status and retrieve the full validation report once complete.

```json
{
  "job_id": "uuid",
  "status": "completed",
  "overall": "FAIL",
  "summary": { "total_rules": 40, "passed": 33, "warnings": 5, "failed": 2 },
  "documents": [...],
  "results": [...],
  "executive_brief": ["...", "...", "...", "...", "..."],
  "conflicts": [...],
  "action_plan": [...]
}
```

### `GET /api/v1/report/{job_id}/pdf`
Download the PDF report (generated on first request, cached thereafter).

### `POST /api/v1/jobs/{job_id}/draft-email`
Generate a professional and urgent email draft for a specific conflict.

```json
{ "conflict_rule_id": "PA-003", "recipient": "lender" }
```

### `GET /api/v1/health`
Health check: `{ "status": "ok" }`

---

## Running Tests

```bash
make test                              # all tests (mocked, no API key needed)
make test-fast                         # fast unit + integration only
make test-e2e                          # end-to-end tests (requires ANTHROPIC_API_KEY + sample docs)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details on testing and development.

---

## Environment Variables

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...       # required
CLAUDE_MODEL=claude-sonnet-4-6     # optional, this is the default
DATABASE_URL=sqlite:///./closecheck.db
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
MAX_FILE_SIZE_MB=25
MAX_FILES_PER_JOB=20
API_KEY=your-secret-api-key

# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=your-secret-api-key
```

---

## Portfolio Note

Built in 10 days as a portfolio piece demonstrating AI document intelligence for real estate closing operations. The project showcases hybrid validation (deterministic rules + Claude API for nuanced extraction), async job processing with FastAPI BackgroundTasks, a pixel-faithful React frontend built from a design reference, and a full 42-rule validation engine covering the major document categories in a residential closing package.
