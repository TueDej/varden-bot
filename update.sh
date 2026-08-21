#!/bin/bash
set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

_banner() {
    echo -e "${CYAN}${BOLD}"
    echo "╔══════════════════════════════════════╗"
    echo "║        🔄  Varden Bot Updater        ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

_step() {
    echo -ne "${BLUE}[..]${NC} $1... "
    if "$@" > /tmp/varden-update-last.log 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo -e "${RED}[✗] Step failed: $1 (see /tmp/varden-update-last.log)${NC}" >&2
        tail -n 20 /tmp/varden-update-last.log >&2 || true
        exit 1
    fi
}

_success() {
    echo -e ""
    echo -e "${GREEN}${BOLD}  ✔ $1${NC}"
}

_banner

_step git pull
source venv/bin/activate
_step pip install -r requirements.txt
_step sudo systemctl restart varden-bot

_success "Varden Bot updated and restarted!"
echo ""
echo -e "  ${BOLD}Quick commands:${NC}"
echo -e "    ${CYAN}Status:${NC}  systemctl status varden-bot"
echo -e "    ${CYAN}Logs:${NC}    journalctl -u varden-bot -f"
echo ""
