# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CloseCheck is an AI-powered pre-close file validator for real estate transactions. Users upload PDF/DOCX closing packages; the backend classifies each document, extracts fields via Claude, runs a rule engine, and returns a structured validation report.

## Commands

### Docker (recommended — runs both services)
```bash
docker-compose up --build          # start everything
docker-compose up --build backend  # rebuild only backend
```

### Backend (local dev)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload      # starts on :8000
```

### Frontend (local dev)
```bash
cd frontend
npm install
npm run dev                        # starts on :5173
```

### Tests
```bash
cd backend
pytest                             # all tests
pytest tests/unit/test_foo.py      # single file
pytest -k "test_name"              # single test by name
```

## Architecture

### Request lifecycle
1. `POST /api/v1/validate` — accepts multipart files, creates a `ValidationJob` (SQLite via SQLAlchemy), saves files to `uploads/{job_id}/`, and kicks off `_process_job` as a FastAPI `BackgroundTask`.
2. Background task pipeline (stubbed/in-progress): `parser.extract_text` → `classifier.classify_document` → field extraction via `llm/client.py` → `validator.run_all_rules` → `report_builder.build_report`.
3. `GET /api/v1/results/{job_id}` — polls job status; frontend polls every 2 s from the Processing page until `completed` or `failed`, then navigates to the Report page.

### Backend layout
- `app/llm/` — all Claude calls go through `client.py` (`claude_json` / `claude_text`). Prompt templates live in `prompts.py` alongside `FIELDS_BY_DOC_TYPE`, which defines what fields to extract per document type.
- `app/services/` — pipeline stages: `parser` (PDF/DOCX text extraction), `classifier` (Claude → doc type), `validator` (runs all rule modules), `report_builder` (aggregates results).
- `app/rules/` — one module per document category (e.g. `title.py`, `loan.py`). Each module defines `BaseRule` subclasses with `rule_id`, `category`, `description`, `severity`, and an async `check(documents)` method. Every module exposes a `RULES` list and a `run(documents)` coroutine. `documents` is a `dict[document_type, extracted_fields_dict]`.
- `app/models/` — SQLAlchemy ORM (`job.py`, `result.py`) and Pydantic schemas (`schemas.py`). Tables are created at startup via `create_tables()`.
- `app/config.py` — `Settings` loaded from `.env`. Key vars: `ANTHROPIC_API_KEY`, `CLAUDE_MODEL` (default `claude-sonnet-4-6`), `DATABASE_URL`, `MAX_FILE_SIZE_MB`, `MAX_FILES_PER_JOB`.

### Frontend layout
Three-page flow: `Upload` → `Processing` → `Report`, each a separate page component under `src/pages/`. All API calls are in `src/api/client.js` (axios). The Vite dev server proxies `/api` to `http://backend:8000` in Docker; for local dev set `VITE_API_BASE_URL` in `frontend/.env`.

### Adding a new validation rule
1. Add the rule class to the relevant module in `app/rules/` (or create a new one).
2. Append an instance to the module's `RULES` list.
3. If it's a new module, import it in `app/services/validator.py` and add it to `ALL_RULE_MODULES`.

### Environment files
- `backend/.env` — `ANTHROPIC_API_KEY`, optionally `CLAUDE_MODEL`, `DATABASE_URL`
- `frontend/.env` — `VITE_API_BASE_URL`, `VITE_API_KEY`

Both are referenced in `docker-compose.yml` via `env_file`.
