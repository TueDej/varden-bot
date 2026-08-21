#!/bin/bash
set -e

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
    echo -e "${BLUE}[${GREEN}✓${BLUE}]${NC} $1"
}

_info() {
    echo -e "${BLUE}[${YELLOW}i${BLUE}]${NC} $1"
}

_success() {
    echo -e ""
    echo -e "${GREEN}${BOLD}  ✔ $1${NC}"
}

_banner

_step "Pulling latest changes..."
git pull > /dev/null 2>&1

_step "Activating virtual environment..."
source venv/bin/activate

_step "Installing/updating Python packages..."
pip install -r requirements.txt > /dev/null 2>&1

_step "Restarting service..."
sudo systemctl restart varden-bot > /dev/null 2>&1

_success "Varden Bot updated and restarted!"
echo ""
echo -e "  ${BOLD}Quick commands:${NC}"
echo -e "    ${CYAN}Status:${NC}  sudo systemctl status varden-bot"
echo -e "    ${CYAN}Logs:${NC}    sudo journalctl -u varden-bot -f"
echo ""
