# CloseCheck — AI Pre-Close File Validator
> MVP Target: 2 weeks | Stack: FastAPI · Python · React · Tailwind · Claude API

---

## 1. Product Overview

CloseCheck is an AI-powered tool that validates real estate transaction files before closing. It ingests closing packages (PDFs, documents, forms), extracts key data, and runs a structured checklist of validation rules to flag missing items, inconsistencies, and risk areas — returning a clear Pass / Warning / Fail report to agents, title officers, or lenders.

**Core value prop:** Replace 2–4 hours of manual file review with a 60-second AI audit.

---

## 2. Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend API | FastAPI (Python 3.11+) | Async, OpenAPI docs auto-generated |
| LLM Processing | Claude API (claude-sonnet-4-6) | Document extraction + rule validation |
| File Parsing | PyMuPDF (fitz), pdfplumber, python-docx | PDF/DOCX ingestion |
| Storage | Local filesystem (MVP) → S3 (post-MVP) | Uploaded files + generated reports |
| Database | SQLite (MVP) → PostgreSQL (post-MVP) | Jobs, results, audit trail |
| Frontend | React 18 + Vite + Tailwind CSS | SPA, no SSR needed for MVP |
| HTTP Client | Axios | Frontend ↔ Backend |
| Auth | API Key header (MVP) → JWT/OAuth (post-MVP) | Simple for now |
| Deployment | Docker Compose | Backend + frontend in containers |

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    FRONTEND (React)                  │
│  Upload UI → Status Tracker → Validation Report      │
└───────────────────────┬─────────────────────────────┘
                        │ REST (multipart + JSON)
┌───────────────────────▼─────────────────────────────┐
│                  BACKEND (FastAPI)                   │
│                                                      │
│  POST /api/v1/validate  ──►  IngestionService        │
│                               │                      │
│                         FileParser (PDF/DOCX)        │
│                               │                      │
│                         DocumentClassifier           │
│                          (Claude API)                │
│                               │                      │
│                         ValidationEngine             │
│                          (rules + Claude API)        │
│                               │                      │
│                         ReportBuilder                │
│                               │                      │
│  GET  /api/v1/results/{id} ◄──┘                      │
│  GET  /api/v1/report/{id}/pdf                        │
└──────────────────────────────────────────────────────┘
```

### Data Flow

1. User uploads closing package (1–N files) via frontend
2. Backend saves files, creates a `ValidationJob` record
3. `IngestionService` extracts raw text from each file
4. `DocumentClassifier` uses Claude to identify document type per file
5. `ValidationEngine` runs rule checks — hybrid: deterministic rules + Claude prompts
6. `ReportBuilder` aggregates findings into a structured JSON report
7. Frontend polls job status and renders the report

---

## 4. Validation Rules

Rules are organized by **document category**. Each rule has a severity: `FAIL` (blocker), `WARNING` (review needed), `INFO` (advisory).

### 4.1 Purchase Agreement
| Rule ID | Description | Severity |
|---------|-------------|----------|
| PA-001 | Buyer and seller names present and consistent across docs | FAIL |
| PA-002 | Property address consistent across all documents | FAIL |
| PA-003 | Purchase price present and matches HUD/CD | FAIL |
| PA-004 | Closing date present and not expired | FAIL |
| PA-005 | Earnest money deposit amount documented | WARNING |
| PA-006 | All required signatures present | FAIL |
| PA-007 | Contingencies noted (inspection, financing, appraisal) | INFO |

### 4.2 Title Commitment / Title Search
| Rule ID | Description | Severity |
|---------|-------------|----------|
| TC-001 | Title commitment present | FAIL |
| TC-002 | Property legal description matches purchase agreement | FAIL |
| TC-003 | Effective date within 6 months | WARNING |
| TC-004 | Schedule B exceptions reviewed and noted | WARNING |
| TC-005 | Open liens flagged | FAIL |
| TC-006 | Judgments or encumbrances identified | FAIL |
| TC-007 | Title insurance amount matches purchase price | WARNING |

### 4.3 Loan / Mortgage Documents
| Rule ID | Description | Severity |
|---------|-------------|----------|
| LN-001 | Loan amount consistent with purchase price and down payment | FAIL |
| LN-002 | Borrower name matches buyer name | FAIL |
| LN-003 | Interest rate and loan type documented | WARNING |
| LN-004 | Promissory note present | FAIL |
| LN-005 | Mortgage/Deed of Trust present | FAIL |
| LN-006 | Loan-to-value ratio within acceptable range | WARNING |

### 4.4 Closing Disclosure / HUD-1
| Rule ID | Description | Severity |
|---------|-------------|----------|
| CD-001 | Closing Disclosure or HUD-1 present | FAIL |
| CD-002 | Cash to close amount documented | FAIL |
| CD-003 | Seller credits match purchase agreement | WARNING |
| CD-004 | Prorated taxes calculated and documented | WARNING |
| CD-005 | Lender fees and origination charges itemized | INFO |
| CD-006 | Total closing costs reasonable (< 5% of purchase price) | WARNING |

### 4.5 Property Documents
| Rule ID | Description | Severity |
|---------|-------------|----------|
| PR-001 | Property tax status — no delinquent taxes | FAIL |
| PR-002 | Survey present (if required by lender) | WARNING |
| PR-003 | HOA documents present (if applicable) | WARNING |
| PR-004 | HOA dues current — no outstanding balance | FAIL |
| PR-005 | Certificate of Occupancy present (new construction) | WARNING |

### 4.6 Insurance
| Rule ID | Description | Severity |
|---------|-------------|----------|
| IN-001 | Homeowner's insurance binder present | FAIL |
| IN-002 | Coverage amount meets or exceeds loan amount | FAIL |
| IN-003 | Lender listed as mortgagee | FAIL |
| IN-004 | Flood insurance present (if flood zone) | FAIL |
| IN-005 | Policy effective on or before closing date | FAIL |

### 4.7 Identity & Compliance
| Rule ID | Description | Severity |
|---------|-------------|----------|
| IC-001 | Government-issued ID for all parties documented | FAIL |
| IC-002 | FIRPTA certificate present (if applicable) | WARNING |
| IC-003 | Wire instructions verified — no changes post-transmission | FAIL |
| IC-004 | Power of Attorney documented and notarized (if applicable) | FAIL |

---

## 5. Claude API Usage

### 5.1 Document Classifier Prompt
```
Classify the following document text into one of these categories:
[purchase_agreement, title_commitment, closing_disclosure, hud1, 
 loan_note, mortgage_deed, insurance_binder, survey, hoa_document,
 tax_certificate, id_document, wire_instructions, other]

Return JSON: {"document_type": "...", "confidence": 0.0-1.0, "notes": "..."}

Document text:
{extracted_text}
```

### 5.2 Validation Extraction Prompt
```
You are a real estate closing specialist. Extract the following fields 
from the document and return structured JSON. If a field is not found, 
return null. Be precise — extract exact values, do not infer.

Fields to extract: {field_list}

Document text:
{extracted_text}
```

### 5.3 Consistency Check Prompt
```
Compare these values extracted from multiple real estate documents 
and identify any inconsistencies. Flag mismatches with explanation.

Values to compare:
{comparison_dict}

Return JSON: {"consistent": bool, "mismatches": [...], "notes": "..."}
```

---

## 6. Folder Structure

```
closecheck/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI app entry point
│   │   ├── config.py                # Settings (env vars via pydantic-settings)
│   │   ├── dependencies.py          # DI: db session, auth, etc.
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── v1/
│   │   │       ├── __init__.py
│   │   │       ├── router.py        # Mounts all v1 routes
│   │   │       ├── validate.py      # POST /validate, GET /results/{id}
│   │   │       └── reports.py       # GET /report/{id}/pdf
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── job.py               # ValidationJob ORM model
│   │   │   ├── result.py            # ValidationResult ORM model
│   │   │   └── schemas.py           # Pydantic request/response schemas
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ingestion.py         # File saving, text extraction orchestration
│   │   │   ├── parser.py            # PDF/DOCX text extraction (PyMuPDF, pdfplumber)
│   │   │   ├── classifier.py        # Claude: document type classification
│   │   │   ├── extractor.py         # Claude: field extraction per doc type
│   │   │   ├── validator.py         # Rule engine: run all rule checks
│   │   │   ├── consistency.py       # Cross-document consistency checks
│   │   │   └── report_builder.py    # Aggregate findings → report JSON
│   │   │
│   │   ├── rules/
│   │   │   ├── __init__.py
│   │   │   ├── base.py              # BaseRule class
│   │   │   ├── purchase_agreement.py
│   │   │   ├── title.py
│   │   │   ├── loan.py
│   │   │   ├── closing_disclosure.py
│   │   │   ├── property.py
│   │   │   ├── insurance.py
│   │   │   └── compliance.py
│   │   │
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── client.py            # Anthropic SDK wrapper, retry logic
│   │   │   └── prompts.py           # All prompt templates
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── database.py          # SQLAlchemy engine + session
│   │       └── migrations/          # Alembic migrations
│   │
│   ├── tests/
│   │   ├── unit/
│   │   │   ├── test_parser.py
│   │   │   ├── test_rules.py
│   │   │   └── test_report_builder.py
│   │   └── integration/
│   │       └── test_validate_endpoint.py
│   │
│   ├── uploads/                     # Temp file storage (gitignored)
│   ├── reports/                     # Generated PDF reports (gitignored)
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Upload.jsx           # File upload + job submission
│   │   │   ├── Processing.jsx       # Job status polling + loading state
│   │   │   └── Report.jsx           # Validation report display
│   │   │
│   │   ├── components/
│   │   │   ├── FileDropzone.jsx     # Drag-and-drop upload area
│   │   │   ├── ProgressBar.jsx      # Processing progress indicator
│   │   │   ├── RuleResult.jsx       # Single rule pass/warn/fail card
│   │   │   ├── CategorySection.jsx  # Grouped rules by document type
│   │   │   ├── SummaryBanner.jsx    # Overall PASS/FAIL banner
│   │   │   └── DownloadButton.jsx   # Download PDF report
│   │   │
│   │   ├── hooks/
│   │   │   ├── useValidationJob.js  # Job submission + polling hook
│   │   │   └── useReport.js         # Report fetching hook
│   │   │
│   │   ├── api/
│   │   │   └── client.js            # Axios instance + API calls
│   │   │
│   │   └── utils/
│   │       ├── severity.js          # Severity color/icon helpers
│   │       └── formatters.js        # Date, currency formatters
│   │
│   ├── public/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .gitignore
└── PROJECT.md                       # This file
```

---

## 7. API Contracts

### POST /api/v1/validate
```json
// Request: multipart/form-data
{
  "files": ["<binary>", ...],       // 1–20 files, PDF or DOCX
  "transaction_type": "residential" // residential | commercial
}

// Response: 202 Accepted
{
  "job_id": "uuid",
  "status": "pending",
  "created_at": "2026-04-19T..."
}
```

### GET /api/v1/results/{job_id}
```json
// Response: 200 OK
{
  "job_id": "uuid",
  "status": "completed",            // pending | processing | completed | failed
  "overall": "WARNING",             // PASS | WARNING | FAIL
  "summary": {
    "total_rules": 42,
    "passed": 35,
    "warnings": 5,
    "failed": 2
  },
  "documents": [
    {
      "filename": "purchase_agreement.pdf",
      "document_type": "purchase_agreement",
      "confidence": 0.97
    }
  ],
  "results": [
    {
      "rule_id": "PA-001",
      "category": "purchase_agreement",
      "description": "Buyer and seller names consistent across docs",
      "severity": "FAIL",
      "status": "FAIL",
      "detail": "Buyer name 'John Smith' in PA but 'J. Smith' in title commitment",
      "documents_referenced": ["purchase_agreement.pdf", "title_commitment.pdf"]
    }
  ],
  "completed_at": "2026-04-19T..."
}
```

---

## 8. Environment Variables

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-sonnet-4-6
DATABASE_URL=sqlite:///./closecheck.db
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
MAX_FILE_SIZE_MB=25
MAX_FILES_PER_JOB=20
API_KEY=your-secret-api-key        # MVP auth

# frontend/.env
VITE_API_BASE_URL=http://localhost:8000
VITE_API_KEY=your-secret-api-key
```

---

## 9. 2-Week MVP Sprint

### Week 1 — Backend Core
| Day | Task |
|-----|------|
| 1 | Project scaffolding, Docker Compose, FastAPI skeleton, DB models |
| 2 | File ingestion: upload endpoint, PDF/DOCX text extraction |
| 3 | Claude integration: document classifier + field extractor |
| 4 | Rule engine: BaseRule + purchase agreement & title rules |
| 5 | Rule engine: loan, closing disclosure, insurance, compliance rules |

### Week 2 — Frontend + Integration
| Day | Task |
|-----|------|
| 6 | Report builder: aggregate results, cross-doc consistency checks |
| 7 | Frontend: Upload page + FileDropzone + API integration |
| 8 | Frontend: Processing/polling page + Report display page |
| 9 | PDF report generation (WeasyPrint or ReportLab) |
| 10 | End-to-end testing, edge cases, demo prep |

---

## 10. Key Decisions & Constraints

- **Hybrid validation**: deterministic rules run first (fast, cheap), Claude only called for extraction and ambiguous checks — keeps API costs low.
- **Stateless jobs for MVP**: no user accounts, jobs identified by UUID.
- **SQLite for MVP**: zero-config, easy to swap for PostgreSQL via `DATABASE_URL`.
- **No async job queue for MVP**: FastAPI `BackgroundTasks` handles processing; Celery/Redis added post-MVP if needed.
- **File size limit**: 25 MB per file, 20 files per job — covers 99% of closing packages.
- **Supported formats**: PDF and DOCX only for MVP.