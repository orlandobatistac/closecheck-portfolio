#!/bin/bash
# ============================================================================
# CloseCheck Production Deployment Script
# ============================================================================
# Usage: bash deploy.sh
#
# This script:
# 1. Backs up the database
# 2. Pulls latest code from git
# 3. Installs/updates Python dependencies
# 4. Creates new database tables
# 5. Deploys systemd service
# 6. Reloads nginx
# 7. Verifies deployment
#
# Prerequisites:
# - You have already created .env.prod with correct secrets
# - You have SSH access to app@<vps-ip>
# - You are in /var/www/closecheck-backend directory
# ============================================================================

set -e  # Exit on first error

echo "🚀 CloseCheck Production Deployment"
echo "===================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo -e "${RED}❌ ERROR: .env.prod not found!${NC}"
    echo "Please create .env.prod with production secrets before running this script."
    echo "Copy from .env.prod.example and update all values."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f app/main.py ]; then
    echo -e "${RED}❌ ERROR: Not in /var/www/closecheck-backend directory!${NC}"
    echo "Please cd to /var/www/closecheck-backend and try again."
    exit 1
fi

echo -e "${YELLOW}[1/7] Backing up database...${NC}"
BACKUP_FILE="closecheck.db.backup.$(date +%Y%m%d-%H%M%S)"
if [ -f closecheck.db ]; then
    cp closecheck.db "$BACKUP_FILE"
    echo -e "${GREEN}✓ Database backed up to: $BACKUP_FILE${NC}"
else
    echo -e "${YELLOW}⚠ No existing database found (new deployment).${NC}"
fi
echo ""

echo -e "${YELLOW}[2/7] Pulling latest code from git...${NC}"
git fetch origin
git pull origin main
echo -e "${GREEN}✓ Code updated${NC}"
echo ""

echo -e "${YELLOW}[3/7] Installing/updating Python dependencies...${NC}"
source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

echo -e "${YELLOW}[4/7] Creating database tables (new tables only)...${NC}"
python << 'EOF'
from app.db.database import create_tables
from sqlalchemy import inspect
from app.db.database import engine

# Create all tables (idempotent — existing tables won't be recreated)
create_tables()

# Verify new tables exist
inspector = inspect(engine)
tables = inspector.get_table_names()

print("Tables in database:")
for table in sorted(tables):
    marker = "✓" if table in ["email_draft_limits", "upload_rate_limits"] else " "
    print(f"  {marker} {table}")

# Verify new tables
if "email_draft_limits" in tables and "upload_rate_limits" in tables:
    print("\n✓ All required tables present")
else:
    print("\n❌ ERROR: Some required tables missing!")
    exit(1)
EOF
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Database creation failed!${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database tables ready${NC}"
echo ""

echo -e "${YELLOW}[5/7] Deploying systemd service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable closecheck.service
sudo systemctl restart closecheck.service
sleep 2
if sudo systemctl is-active --quiet closecheck.service; then
    echo -e "${GREEN}✓ systemd service deployed and running${NC}"
else
    echo -e "${RED}❌ systemd service failed to start!${NC}"
    echo "Run: sudo journalctl -u closecheck.service -n 50"
    exit 1
fi
echo ""

echo -e "${YELLOW}[6/7] Reloading nginx...${NC}"
sudo nginx -t > /dev/null 2>&1
if [ $? -eq 0 ]; then
    sudo systemctl reload nginx
    echo -e "${GREEN}✓ nginx reloaded successfully${NC}"
else
    echo -e "${RED}❌ nginx config test failed!${NC}"
    echo "Run: sudo nginx -t"
    exit 1
fi
echo ""

echo -e "${YELLOW}[7/7] Verifying deployment...${NC}"
echo ""

# Check systemd status
echo "  Checking systemd service..."
if sudo systemctl is-active --quiet closecheck.service; then
    echo -e "  ${GREEN}✓ Service is running${NC}"
else
    echo -e "  ${RED}❌ Service is not running${NC}"
    exit 1
fi

# Check for recent errors in logs
echo "  Checking logs for errors..."
ERROR_COUNT=$(sudo journalctl -u closecheck.service -n 100 --no-pager | grep -i "error\|exception" | grep -v "401\|429" | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    echo -e "  ${GREEN}✓ No critical errors in logs${NC}"
else
    echo -e "  ${YELLOW}⚠ Found $ERROR_COUNT errors (may be normal)${NC}"
    echo "    Run: sudo journalctl -u closecheck.service -f"
fi

echo ""
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test the API from your local machine:"
echo "     curl https://api.closecheck.example/health"
echo ""
echo "  2. Test with API key:"
echo "     API_KEY=\$(grep API_KEY .env.prod | cut -d= -f2)"
echo "     curl -X POST https://api.closecheck.example/api/v1/validate \\"
echo "       -H \"X-API-Key: \$API_KEY\" \\"
echo "       -F \"files=@test.pdf\" \\"
echo "       -F \"transaction_type=residential\""
echo ""
echo "  3. Test rate limiting (2nd upload should return 429):"
echo "     curl -X POST https://api.closecheck.example/api/v1/validate \\"
echo "       -H \"X-API-Key: \$API_KEY\" \\"
echo "       -F \"files=@test2.pdf\" \\"
echo "       -F \"transaction_type=residential\""
echo ""
echo "  4. Monitor logs:"
echo "     sudo journalctl -u closecheck.service -f"
echo ""
