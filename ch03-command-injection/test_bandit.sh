#!/bin/bash
# Bandit security scanning script for Command Injection chapter

echo "=========================================="
echo "Bandit Security Scan - Command Injection"
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
echo "  - B602: shell=True detected in subprocess.run()"
echo "  - B605: os.popen() usage detected"
echo ""
echo -e "${GREEN}SECURE:${NC}"
echo "  - No high/medium severity issues"
echo "  - Uses subprocess.run() with shell=False"
echo "=========================================="
