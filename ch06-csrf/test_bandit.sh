#!/bin/bash
# Bandit security scanning script for CSRF chapter

echo "=========================================="
echo "Bandit Security Scan - CSRF"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Installing bandit if not present..."
pip install -q bandit 2>/dev/null || pip3 install -q bandit 2>/dev/null

echo ""
echo "=== Scanning VULNERABLE code ==="
echo ""
bandit -r vulnerable/ -f txt -ll || true

echo ""
echo "=== Scanning SECURE code ==="
echo ""
bandit -r secure/ -f txt -ll || true

echo ""
echo "=========================================="
echo "Expected Results:"
echo "----------------------------------------"
echo -e "${RED}VULNERABLE:${NC}"
echo "  - B105: Hardcoded secret key 'secret'"
echo "  - B201: Flask debug=True enabled"
echo ""
echo -e "${GREEN}SECURE:${NC}"
echo "  - B105: May still detect hardcoded secret (should use env vars)"
echo "  - No debug=True in production"
echo "=========================================="
