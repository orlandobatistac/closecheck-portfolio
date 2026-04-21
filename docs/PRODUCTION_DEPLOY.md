# CloseCheck Production Deploy

## Purpose

This document defines the production deployment architecture for CloseCheck and overrides the default assumption that production should use the local Docker development setup.

Agents working on deployment, CI/CD, environment configuration, or infrastructure should treat this as the source of truth for production.

---

## Production Topology

CloseCheck production is split across two public origins:

1. `app.<domain>` or equivalent static hosting domain for the frontend
2. `api.<domain>` on the VPS for the backend API

Example:

- Frontend: `https://app.closecheck.example`
- Backend: `https://api.closecheck.example`

The frontend is not hosted on the VPS.
The backend is hosted on the VPS.

---

## Current VPS Architecture Pattern

This VPS already follows a consistent production pattern across other projects.

### Server layout

Application code is stored under `/var/www`.

Examples already present on the VPS:

- `/var/www/SHIOL-PLUS`
- `/var/www/deducttax-api`
- `/var/www/patternlottopro`
- `/var/www/workhub-backend`

### Reverse proxy

`nginx` is the public entrypoint.

Responsibilities:

- terminate TLS with Certbot certificates
- route requests by domain
- proxy backend traffic to localhost ports
- serve static frontend files for projects that live on the VPS

### App runtime

The dominant production runtime pattern is:

- `systemd` service per backend app
- `uvicorn` started from a project-local Python virtualenv
- backend bound to a localhost port
- `nginx` proxies the public API domain to that localhost port

This is the pattern CloseCheck should follow for the backend.

---

## CloseCheck Production Architecture

### Frontend

Production frontend hosting should be static hosting outside the VPS.

Accepted examples:

- Vercel
- Netlify
- Cloudflare Pages
- S3 + CDN
- any equivalent static hosting platform

The frontend build should publish static assets only.

The frontend must call the production API using the public backend origin, for example:

- `VITE_API_BASE_URL=https://api.<domain>`

The frontend should not be deployed as a long-running VPS process unless this document is explicitly revised.

### Backend

Production backend hosting is on the VPS.

Recommended project location:

- `/var/www/closecheck-backend`

Recommended runtime shape:

- Python virtualenv inside the project directory
- FastAPI app served by `uvicorn`
- localhost-only bind, for example `127.0.0.1:80xx`
- `systemd` unit to manage process lifecycle
- `nginx` site config for `api.<domain>`

### Database and storage

The current app uses SQLite and filesystem-backed uploads/reports.

Production should keep these concerns on the VPS backend side:

- SQLite database file
- uploaded source files
- generated reports
- any backend-side caches or artifacts

These paths should remain private to the server and must not be exposed directly by the frontend host.

---

## What Production Is Not

Production is not the local Docker Compose development stack described elsewhere in the repository.

That means:

- do not assume the frontend container is the production frontend
- do not assume the frontend is reverse-proxied from the same host as the backend
- do not assume `docker-compose up` defines the real production topology

The current `docker-compose.yml` remains useful for local development and possibly temporary preview environments, but it is not the source of truth for production deployment architecture.

---

## Deployment Rules For Agents

When editing deployment-related files, agents should follow these rules:

1. Treat this document as higher priority than README wording or local dev defaults.
2. Keep the frontend and backend deployment targets separated.
3. Prefer VPS backend deployment via `systemd` plus `nginx`, not Docker-first production assumptions.
4. Prefer static hosting guidance for the frontend.
5. Configure CORS, environment variables, and API URLs to reflect cross-origin production between `app.<domain>` and `api.<domain>`.
6. Do not introduce infrastructure guidance that assumes the frontend must live on the VPS unless explicitly requested.

---

## Immediate Implications For Future Work

Any future production work should align with this architecture, including:

- backend deploy scripts
- GitHub Actions or other CI/CD workflows
- `.env.production` or secret configuration
- `nginx` site examples
- `systemd` service examples
- frontend production environment variables
- FastAPI CORS hardening for the real frontend origin

If another document conflicts with this one, this document wins for production decisions.