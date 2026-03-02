#!/bin/bash
# Bandit security scanning script for SQL Injection chapter

echo "=========================================="
echo "Bandit Security Scan - SQL Injection"
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
python -m bandit -r vulnerable/ -f txt -ll || true

echo ""
echo "=== Scanning SECURE code ==="
echo ""
python -m bandit -r secure/ -f txt -ll || true

echo ""
echo "=========================================="
echo "Expected Results:"
echo "----------------------------------------"
echo -e "${RED}VULNERABLE:${NC}"
echo "  - B608: Hardcoded SQL string (string formatting in queries)"
echo "  - B201: Flask debug=True detected"
echo "  - B105: Hardcoded password/secret_key"
echo ""
echo -e "${GREEN}SECURE:${NC}"
echo "  - No B608 issues (uses parameterized queries/ORM)"
echo "  - May have B105 for secret_key (environment variable recommended)"
echo "=========================================="
