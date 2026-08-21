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
    echo "║        🤖  Varden Bot Installer      ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

_step() {
    echo -e "${BLUE}[${GREEN}✓${BLUE}]${NC} $1"
}

_info() {
    echo -e "${BLUE}[${YELLOW}i${BLUE}]${NC} $1"
}

_error() {
    echo -e "${RED}[✗] $1${NC}" >&2
}

_success() {
    echo -e ""
    echo -e "${GREEN}${BOLD}  ✔ $1${NC}"
}

if [ -z "$1" ]; then
    _banner
    echo -e "  ${YELLOW}Usage:${NC} $0 <bot-token> [gf-user-id] [my-user-id]"
    echo -e ""
    echo -e "  ${CYAN}Arguments:${NC}"
    echo -e "    bot-token    ${NC}Telegram Bot Token from BotFather"
    echo -e "    gf-user-id   ${NC}User ID for pickup messages (default: 190637471)"
    echo -e "    my-user-id   ${NC}User ID for notifications (default: 2059317327)"
    exit 1
fi

TOKEN=$1
GF_ID=${2:-190637471}
MY_ID=${3:-2059317327}

_banner

echo -e "  ${BOLD}Configuration:${NC}"
echo -e "    ${CYAN}GF User ID:${NC}  $GF_ID"
echo -e "    ${CYAN}My User ID:${NC}  $MY_ID"
echo -e ""

_step "Installing system dependencies (python3, pip, venv)..."
sudo apt update -qq && sudo apt install -y -qq python3 python3-pip python3-venv > /dev/null 2>&1

_step "Creating virtual environment..."
python3 -m venv venv > /dev/null 2>&1

_step "Activating virtual environment..."
source venv/bin/activate

_step "Installing Python packages..."
pip install -r requirements.txt > /dev/null 2>&1

_step "Creating systemd service..."
sudo tee /etc/systemd/system/varden-bot.service > /dev/null <<EOF
[Unit]
Description=Varden Telegram Bot
After=network.target

[Service]
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python3 bot.py
Environment=TELEGRAM_BOT_TOKEN=$TOKEN
Environment=GF_USER_ID=$GF_ID
Environment=MY_USER_ID=$MY_ID
Restart=always

[Install]
WantedBy=multi-user.target
EOF

_step "Enabling and starting service..."
sudo systemctl daemon-reload > /dev/null 2>&1
sudo systemctl enable varden-bot > /dev/null 2>&1
sudo systemctl start varden-bot > /dev/null 2>&1

_success "Varden Bot installed and running!"
echo ""
echo -e "  ${BOLD}Quick commands:${NC}"
echo -e "    ${CYAN}Status:${NC}  sudo systemctl status varden-bot"
echo -e "    ${CYAN}Logs:${NC}    sudo journalctl -u varden-bot -f"
echo -e "    ${CYAN}Restart:${NC} sudo systemctl restart varden-bot"
echo ""
