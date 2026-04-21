# CloseCheck Architecture

## High-Level Overview

CloseCheck is a three-tier application:
1. **Frontend (React)** — User uploads documents, polls for results, views reports
2. **Backend (FastAPI)** — Processes files, runs rule engine, generates reports via Claude
3. **Database (SQLite)** — Stores job metadata, results, and audit trail

---

## Request Lifecycle

```
┌──────────────────────────────────────────────────────────────┐
│ FRONTEND                                                       │
│ User clicks "Validate"                                         │
└────────────────────┬─────────────────────────────────────────┘
                     │ POST /api/v1/validate (multipart)
┌────────────────────▼─────────────────────────────────────────┐
│ BACKEND                                                        │
│                                                                │
│ 1. Create ValidationJob → DB (status=PENDING)                │
│ 2. Add BackgroundTask(_process_job)                          │
│ 3. Return job_id (202 Accepted)                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     └─────────────────────────┐
                                               │
┌──────────────────────────────────────────────▼────────────────┐
│ BACKGROUND TASK (_process_job)                                │
│                                                                │
│ Phase 1: Ingestion                                            │
│ ├─ save_uploaded_files() → backend/uploads/{job_id}/         │
│ ├─ extract_text() → PDF/DOCX parser (PyMuPDF + python-docx)  │
│ └─ save_extracted_texts()                                    │
│                                                                │
│ Phase 2: Classification                                      │
│ ├─ classify_document() → Claude API + CLASSIFIER_PROMPT      │
│ └─ save_classifications()                                    │
│                                                                │
│ Phase 3: Field Extraction                                    │
│ ├─ extract_fields() → Claude API + FIELD_EXTRACTOR_PROMPT    │
│ └─ save_fields()                                             │
│                                                                │
│ Phase 4: Validation Rules                                    │
│ ├─ run_all_rules() → 40 BaseRule subclasses (async)          │
│ ├─ run_consistency_checks() → cross-doc validations          │
│ └─ results sorted by severity (FAIL → WARNING → PASS)        │
│                                                                │
│ Phase 5: Report Generation                                   │
│ ├─ build_report() aggregates results                         │
│ ├─ _get_executive_brief() → Claude API (5 bullets)           │
│ ├─ _get_action_plan() → Claude API (prioritized to-do)       │
│ ├─ save_report() → backend/reports/{job_id}.json             │
│ ├─ Update job.status = COMPLETED                            │
│ └─ Log elapsed time + overall verdict                        │
│                                                                │
└────────────────────┬─────────────────────────────────────────┘
                     │ Update DB
        ┌────────────▼─────────────┐
        │ ValidationJob.status     │
        │ .overall (PASS/WARNING)  │
        │ .error_message (if FAIL) │
        │ .completed_at            │
        └──────────────────────────┘

                     │
┌────────────────────▼─────────────────────────────────────────┐
│ FRONTEND                                                       │
│ GET /api/v1/results/{job_id} (polls every 2s)                │
│ When status=completed, navigate to Report page                │
│ Display executive_brief, conflicts, action_plan              │
└────────────────────────────────────────────────────────────────┘
```

---

## Backend Modules

### `app/api/`
RESTful API routes organized by domain.

**`v1/validate.py`**
- `POST /api/v1/validate` — Kick off a validation job
- `GET /api/v1/results/{job_id}` — Poll job status and retrieve results
- `POST /api/v1/jobs/{job_id}/draft-email` — Generate email drafts for conflicts

**`v1/reports.py`**
- `GET /api/v1/report/{job_id}/pdf` — Download cached or generated PDF report

### `app/services/`
Business logic for each pipeline stage.

**`parser.py`** → `extract_text(file_path) -> str`
- Loads PDF or DOCX using PyMuPDF or python-docx
- Returns first 8000 characters of text

**`classifier.py`** → `classify_document(text) -> DocumentClassification`
- Calls Claude API with `CLASSIFIER_PROMPT`
- Returns `document_type` (e.g., "purchase_agreement") + `confidence` (0.0–1.0)

**`extractor.py`** → `extract_fields(doc_type, text) -> dict`
- Calls Claude API with `FIELD_EXTRACTOR_PROMPT`
- Maps document type → expected fields via `FIELDS_BY_DOC_TYPE` in `llm/prompts.py`
- Returns `{field_name: value}` dict (null for missing fields)

**`validator.py`** → `run_all_rules(documents) -> List[RuleResult]`
- Runs all rule modules asynchronously
- Combines results and sorts by severity (FAIL first)
- See "Rules Engine" section below

**`consistency.py`** → `run_consistency_checks(fields) -> List[RuleResult]`
- Cross-document validation (e.g., purchase price in PA vs CD)
- Returns synthetic RuleResult objects for conflicts

**`report_builder.py`** → `build_report(...) -> dict`
- Aggregates rule results into the final JSON structure
- Calls Claude for `executive_brief` (5 bullets) and `action_plan` (prioritized tasks)
- Builds `conflicts` array with cross-doc mismatches
- Tries/except wraps Claude calls to prevent job failures on brief/plan errors

**`pdf_generator.py`** → `generate_pdf(report, output_path)`
- Uses ReportLab to create a 3-page PDF report
- Includes summary, rule results, and conflicts

**`ingestion.py`**
- File I/O helpers: `save_uploaded_files()`, `load_report()`, `load_fields()`, etc.

### `app/rules/`
Validation rules, one module per document category.

**Base class:** `BaseRule` in `base.py`
```python
class BaseRule:
    rule_id: str          # e.g., "PA-001"
    category: str         # e.g., "purchase_agreement"
    description: str      # Human-readable rule name
    severity: Severity    # FAIL, WARNING, INFO
    
    async def check(self, documents: dict) -> RuleResult:
        # documents is {doc_type: {field: value}}
        # Return RuleResult(self, status, detail)
```

**Modules:**
- **`purchase_agreement.py`** — PA-001 to PA-007 (7 rules)
- **`title.py`** — TC-001 to TC-007 (7 rules)
- **`loan.py`** — LN-001 to LN-006 (6 rules)
- **`closing_disclosure.py`** — CD-001 to CD-006 (6 rules)
- **`property_docs.py`** — PR-001 to PR-005 (5 rules)
- **`insurance.py`** — IN-001 to IN-005 (5 rules)
- **`compliance.py`** — IC-001 to IC-004 (4 rules)

**Total:** 40 rules

### `app/llm/`
Claude API integration.

**`client.py`**
- `get_client()` — Lazy-init Anthropic client
- `claude_json(prompt, max_tokens) -> dict` — JSON mode (parses response as JSON)
- `claude_text(prompt, system, max_tokens) -> str` — Raw text mode
- Error handling: `ClaudeResponseError` for invalid/missing JSON

**`prompts.py`**
- `CLASSIFIER_PROMPT` — Classify a document into a type + confidence
- `FIELD_EXTRACTOR_PROMPT` — Extract fields for a given document type
- `EXECUTIVE_BRIEF_PROMPT` — 5 bullet summary of rule failures
- `ACTION_PLAN_PROMPT` — Prioritized to-do list for resolving conflicts
- `FIELDS_BY_DOC_TYPE` — Maps each document type to expected fields

### `app/models/`
Data models.

**`job.py`** — SQLAlchemy ORM
- `ValidationJob` table: id, status, overall, file_count, created_at, completed_at, error_message

**`schemas.py`** — Pydantic schemas for API responses
- `JobResultResponse` — Full job + results payload
- `RuleResultSchema` — Single rule result
- `ConflictCard` — Cross-doc mismatch
- `ActionItem` — Action plan item

### `app/db/`
Database setup and session management.

**`database.py`**
- `SessionLocal` — SQLAlchemy session factory
- `Base` — SQLAlchemy declarative base for ORM models
- `get_db()` — Dependency for FastAPI route handlers
- `create_tables()` — Called on app startup

### `app/config.py`
Settings loaded from `.env`:
```python
ANTHROPIC_API_KEY          # Required
CLAUDE_MODEL               # Default: claude-sonnet-4-6
DATABASE_URL               # Default: sqlite:///./closecheck.db
UPLOAD_DIR                 # Default: ./uploads
REPORTS_DIR                # Default: ./reports
MAX_FILE_SIZE_MB           # Default: 25
MAX_FILES_PER_JOB          # Default: 20
API_KEY                    # Default: dev-key
```

---

## Frontend Structure

### Three-Page Flow

```
Upload (pages/Upload.jsx)
   ↓ (submit files)
Processing (pages/Processing.jsx)
   ↓ (polls every 2s, polls /api/v1/results/{job_id})
   ↓ (when status=completed, navigate to /report/{job_id})
Report (pages/Report.jsx)
   ↓ (displays summary, conflicts, action plan, email drafts)
```

### API Client

**`src/api/client.js`** — Axios wrapper
- `getResults(jobId)` — GET /api/v1/results/{jobId}
- `validateFiles(files, txnType)` — POST /api/v1/validate
- `draftEmail(jobId, conflictId, recipient)` — POST /api/v1/jobs/{jobId}/draft-email
- `getPdfReport(jobId)` — GET /api/v1/report/{jobId}/pdf

### Styling

- **CSS Framework:** Tailwind CSS
- **Bundler:** Vite
- **Dev Server:** Vite (http://localhost:5173)
- **Production Build:** `npm run build` → `dist/`

---

## Data Flow Example: Martinez Test

1. **User uploads** `Martinez_PA.pdf`, `Martinez_CD.pdf`, `Martinez_TC.pdf`
2. **Parser extracts text** from each PDF
3. **Classifier identifies:**
   - PA.pdf → "purchase_agreement" (confidence 0.92)
   - CD.pdf → "closing_disclosure" (confidence 0.95)
   - TC.pdf → "title_commitment" (confidence 0.88)
4. **Extractor pulls fields:**
   - PA: `buyer_name: "Carlos Martinez"`, `purchase_price: 385000`
   - CD: `purchase_price: 387500` (mismatch!)
   - TC: `legal_description: "...", property_address: "123 Main St"`
5. **Rules run:**
   - PA-001 (buyer name consistency): Check if PA buyer matches other docs → FAIL (Carlos vs. Carlos Martínez)
   - PA-003 (price consistency): 385000 vs. 387500 → FAIL
   - TC-001 (title present): ✓ PASS
   - ... (38 more rules)
6. **Report builds:**
   - overall = "FAIL"
   - conflicts = [{rule_id: "PA-001", ...}, {rule_id: "PA-003", ...}]
   - executive_brief = ["Buyer name mismatch across documents", ...]
   - action_plan = [{title: "Reconcile buyer name", urgency: "now", ...}, ...]
7. **Frontend displays:**
   - Red banner: "Blocked — closing cannot proceed"
   - Conflict cards side-by-side: "Carlos Martinez" (PA) vs. "Carlos Martínez" (commitment)
   - Action plan: 2 urgent tasks
   - Email drafts: "Please reconcile buyer name discrepancy..."

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Invalid file type | HTTP 400, job rejected |
| File > MAX_FILE_SIZE_MB | HTTP 400, job rejected |
| > MAX_FILES_PER_JOB | HTTP 400, job rejected |
| Parser crash (corrupt PDF) | Job status = FAILED, error_message logged |
| Claude API timeout | Job status = FAILED, error_message logged |
| Executive brief JSON invalid | Logged as warning; still completes job |
| Action plan generation fails | Logged as warning; still completes job |

---

## Deployment

Production deployment is defined in [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md).

### Local Docker Development
```bash
docker-compose up --build
```
Runs:
- **Backend:** uvicorn on port 8000
- **Frontend:** Vite + nginx proxy on port 5173
- Both services share `.env` files via `env_file` in compose config

This setup is for local development and preview-style environments, not the source of truth for production topology.

### Production

- **Frontend:** static hosting on a separate public origin such as `app.<domain>`
- **Backend:** VPS-hosted FastAPI service on `api.<domain>`
- **Reverse proxy:** `nginx` terminates TLS and proxies the API domain to a localhost backend port
- **Process manager:** `systemd` manages the backend service lifecycle
- **Runtime model:** project-local virtualenv + `uvicorn`, bound to localhost only

### Local Development
```bash
make dev-backend    # Terminal 1
make dev-frontend   # Terminal 2
```

### Environment
- **Development:** `CLAUDE_MODEL=claude-sonnet-4-6` (default)
- **Production:** configure real frontend/backend origins, CORS, secrets, and server paths according to [PRODUCTION_DEPLOY.md](PRODUCTION_DEPLOY.md)

---

## Testing

### Unit Tests
- Test individual rules, services, API endpoints
- Mocked Claude API (no `ANTHROPIC_API_KEY` required)
- Fast (~1–2 seconds total)

### Integration Tests
- Test rule combinations, report building, consistency checks
- Mocked Claude
- Medium speed (~5 seconds)

### E2E Tests
- Use actual sample documents (Martinez_test)
- Call real Claude API (requires `ANTHROPIC_API_KEY`)
- Slow (~30 seconds per test)

Run with:
```bash
make test           # All tests (mocked)
make test-fast      # Unit + integration only
make test-e2e       # E2E with real Claude
```

---

## Future Enhancements

1. **Caching** — Cache document classifications + field extractions
2. **Streaming** — Stream results to frontend as phases complete (vs. polling)
3. **Multi-language** — Support non-English closing documents
4. **Custom rules** — User-defined rules via UI
5. **Audit trail** — Full log of all rule violations + resolutions
6. **Batch processing** — Submit 1000s of files, get CSV report
7. **Mobile app** — React Native companion for field verification on-site
