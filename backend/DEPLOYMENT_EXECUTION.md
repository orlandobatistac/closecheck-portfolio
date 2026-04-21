# CloseCheck Production Deployment — Execution Guide

This guide walks through deploying the 3 P0 protections (API key validation, email draft limiting, upload rate limiting) to the VPS.

**Prerequisites:**
- SSH access to VPS (`ssh app@<vps-ip>`)
- VPS directory structure: `/var/www/closecheck-backend/` with Python virtualenv
- nginx already configured and running
- Certbot TLS certificates in place for `api.closecheck.example`

---

## 1. Pre-Deployment Checks (Local — Before Touching VPS)

```bash
# Run full test suite
cd C:\Dev\apps\closecheck\backend
python -m pytest tests/unit/test_auth.py tests/unit/test_email_limit.py tests/unit/test_upload_rate_limit.py -v

# Expected: 34/34 PASSED, 0 warnings
# Exit code: 0
```

✅ **Status:** All tests passing (verified in conversation history)

---

## 2. Prepare Deployment Files (Local)

These files are now ready in the repo:
- `closecheck.service` — systemd unit file (→ copy to VPS)
- `nginx-api.conf` — nginx site config template (→ copy to VPS)
- `.env.prod.example` — environment template (→ guide for creating `.env.prod`)

---

## 3. Prepare VPS Environment

### 3.1 Create .env.prod on VPS

```bash
ssh app@<vps-ip>
cd /var/www/closecheck-backend

# Copy template
cp .env.prod.example .env.prod

# Edit with production secrets
nano .env.prod
# Change these (marked <CHANGE-ME> or <SECRET>):
#   API_KEY=<GENERATE-32-CHAR-RANDOM-SECRET>
#   ANTHROPIC_API_KEY=sk-ant-<your-claude-key>
#   CORS_ALLOW_ORIGINS=["https://app.closecheck.example"]

# Set secure permissions
chmod 600 .env.prod
ls -la .env.prod
# Expected: -rw------- 1 app app
```

### 3.2 Backup Current Database

```bash
cd /var/www/closecheck-backend
cp closecheck.db closecheck.db.backup.$(date +%Y%m%d-%H%M%S)
ls -lh closecheck.db*
# Expected: Two files — original + backup
```

---

## 4. Update Code on VPS

```bash
cd /var/www/closecheck-backend

# Fetch latest changes
git fetch origin
git pull origin main

# Activate virtualenv
source venv/bin/activate

# Install dependencies (if requirements.txt changed)
pip install -r requirements.txt

# Test imports
python << 'EOF'
from app.db.database import create_tables
from app.api.v1.validate import router
from app.api.deps.auth import verify_api_key
from app.api.deps.email_limit import check_email_draft_limit
from app.api.deps.upload_rate_limit import check_upload_rate_limit
print("✓ All modules import successfully")
EOF
```

---

## 5. Setup systemd Service

### 5.1 Copy systemd File

```bash
# From your local repo, copy to VPS:
scp closecheck.service app@<vps-ip>:/tmp/

# On VPS
cd /tmp
sudo cp closecheck.service /etc/systemd/system/closecheck.service

# Verify
sudo ls -la /etc/systemd/system/closecheck.service
```

### 5.2 Enable and Start Service

```bash
# On VPS
sudo systemctl daemon-reload
sudo systemctl enable closecheck.service
sudo systemctl restart closecheck.service

# Verify status
sudo systemctl status closecheck.service
# Expected: ● closecheck.service - CloseCheck API
#             Loaded: loaded (/etc/systemd/system/closecheck.service)
#             Active: active (running) since ...

# Check logs
sudo journalctl -u closecheck.service -n 50
# Expected: No 500 errors, startup complete
```

---

## 6. Setup nginx Reverse Proxy

### 6.1 Copy nginx Config

```bash
# From your local repo, copy to VPS:
scp nginx-api.conf app@<vps-ip>:/tmp/

# On VPS
cd /tmp
sudo cp nginx-api.conf /etc/nginx/sites-available/api.closecheck.example

# Enable site
sudo ln -s /etc/nginx/sites-available/api.closecheck.example \
           /etc/nginx/sites-enabled/api.closecheck.example

# Verify symlink
sudo ls -la /etc/nginx/sites-enabled/ | grep closecheck
```

### 6.2 Verify and Reload nginx

```bash
# Test nginx config
sudo nginx -t
# Expected: nginx: configuration file test is successful

# Reload nginx
sudo systemctl reload nginx

# Verify nginx running
sudo systemctl status nginx
# Expected: active (running)
```

---

## 7. Post-Deployment Verification

### 7.1 Health Checks

```bash
# Test endpoint responding (from your local machine)
curl https://api.closecheck.example/health
# Expected: {"status": "ok", ...}

# Test auth rejection (without X-API-Key)
curl -X POST https://api.closecheck.example/api/v1/validate \
  -F "files=@test.pdf" \
  -F "transaction_type=residential"
# Expected: 401 Unauthorized
# Body: {"detail": "Missing or invalid API key"}

# Test auth success (with X-API-Key)
API_KEY="<your-prod-api-key-from-.env.prod>"
curl -X POST https://api.closecheck.example/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test.pdf" \
  -F "transaction_type=residential"
# Expected: 202 Accepted
# Body: {"job_id": "...", "status": "queued"}
```

### 7.2 Rate Limit Tests

```bash
API_KEY="<your-prod-api-key>"

# First upload (should succeed)
curl -X POST https://api.closecheck.example/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test1.pdf" \
  -F "transaction_type=residential"
# Expected: 202 Accepted + job_id

# Second upload immediately (should be rate-limited)
curl -X POST https://api.closecheck.example/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test2.pdf" \
  -F "transaction_type=residential"
# Expected: 429 Too Many Requests
# Body: {"detail": "Rate limit exceeded. Please wait Xs before...", "retry_after_seconds": X}

# Wait 11 seconds
sleep 11

# Third upload (should succeed)
curl -X POST https://api.closecheck.example/api/v1/validate \
  -H "X-API-Key: $API_KEY" \
  -F "files=@test3.pdf" \
  -F "transaction_type=residential"
# Expected: 202 Accepted + job_id
```

### 7.3 Database Integrity

```bash
# On VPS — verify new tables exist
cd /var/www/closecheck-backend
python << 'EOF'
from app.db.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()
print("All tables in DB:")
for t in sorted(tables):
    print(f"  - {t}")

# Verify new tables
assert "email_draft_limits" in tables, "❌ email_draft_limits not found"
assert "upload_rate_limits" in tables, "❌ upload_rate_limits not found"
print("\n✓ New rate-limit tables verified in DB")
EOF
```

### 7.4 Monitor Logs

```bash
# On VPS — watch service logs in real-time
sudo journalctl -u closecheck.service -f

# In another terminal, run test requests (from local machine)
# You should see request logs with 401, 202, 429 status codes
```

---

## 8. Configure Frontend (Static Hosting)

If not already done, update your static hosting (Vercel, Netlify, etc.) with:

```
VITE_API_BASE_URL=https://api.closecheck.example
VITE_API_KEY=<same-api-key-from-.env.prod>
```

Then rebuild and deploy frontend.

---

## 9. Rollback Procedure (If Needed)

### Option A: Revert Code

```bash
cd /var/www/closecheck-backend
git revert HEAD --no-edit
# OR (if revert too complex)
git checkout <previous-commit-hash>

source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart closecheck.service
```

### Option B: Restore Database

```bash
cd /var/www/closecheck-backend
cp closecheck.db.backup.<timestamp> closecheck.db
sudo systemctl restart closecheck.service
```

---

## 10. Success Criteria Checklist

```
✅ Code & Tests
  [✓] All 34 tests pass locally
  [✓] Code reviewed and approved
  
✅ VPS Preparation
  [ ] .env.prod created with correct secrets
  [ ] chmod 600 .env.prod
  [ ] Database backup created
  
✅ Deployment
  [ ] Git pull executed
  [ ] systemd service enabled and running
  [ ] nginx config deployed and reloaded
  [ ] journalctl logs show no 500 errors
  
✅ Verification
  [ ] /health → 200 OK
  [ ] POST without X-API-Key → 401
  [ ] POST with X-API-Key → 202
  [ ] Second upload immediately → 429 (rate limited)
  [ ] Third upload after 11s → 202 (allowed)
  [ ] Database has email_draft_limits + upload_rate_limits tables
  
✅ Frontend
  [ ] Build successful
  [ ] Deploy to static hosting successful
  [ ] VITE_API_BASE_URL set correctly

Deployment Status: ____________  Date: ___________  Deployed By: __________
```

---

## Troubleshooting

### Issue: "Module not found" after git pull
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Permission denied on .env.prod
```bash
chmod 600 /var/www/closecheck-backend/.env.prod
chown app:app /var/www/closecheck-backend/.env.prod
```

### Issue: systemd service won't start
```bash
sudo journalctl -u closecheck.service -n 100
# Look for the error message and fix accordingly
# Common: ANTHROPIC_API_KEY not set, PORT already in use
```

### Issue: 403 from nginx (CORS issue)
```bash
# Verify nginx config was updated correctly
sudo cat /etc/nginx/sites-available/api.closecheck.example | grep -A5 "CORS\|Access-Control"

# Check frontend origin matches:
# CORS_ALLOW_ORIGINS in .env.prod should match frontend's actual domain
```

---

## Commands Reference

| Task | Command |
|------|---------|
| Deploy code | `cd /var/www/closecheck-backend && git pull origin main` |
| Start service | `sudo systemctl restart closecheck.service` |
| Check status | `sudo systemctl status closecheck.service` |
| View logs | `sudo journalctl -u closecheck.service -f` |
| Reload nginx | `sudo systemctl reload nginx` |
| Test nginx config | `sudo nginx -t` |
| Create DB backup | `cp closecheck.db closecheck.db.backup.$(date +%Y%m%d-%H%M%S)` |
| Restore DB | `cp closecheck.db.backup.<timestamp> closecheck.db` |

---

**Questions?** Refer back to the deployment plan in `/memories/session/prod-deploy-plan.md`
