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
    echo "║        🤖  Varden Bot Installer      ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

_step() {
    local desc=$1
    shift
    echo -ne "${BLUE}[..]${NC} ${desc}... "
    if "$@" > /tmp/varden-install-last.log 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        _error "Step failed: ${desc} (see /tmp/varden-install-last.log)"
        tail -n 20 /tmp/varden-install-last.log >&2 || true
        exit 1
    fi
}

_error() {
    echo -e "${RED}[✗] $1${NC}" >&2
}

_success() {
    echo -e ""
    echo -e "${GREEN}${BOLD}  ✔ $1${NC}"
}

_banner

if [ $# -lt 1 ]; then
    echo -e "  ${YELLOW}Usage:${NC} $0 <bot-token> [gf-user-id] [my-user-id]"
    echo -e ""
    echo -e "  ${CYAN}Arguments:${NC}"
    echo -e "    bot-token    Telegram Bot Token from BotFather"
    echo -e "    gf-user-id   User ID for pickup messages"
    echo -e "    my-user-id   User ID for notifications and admin commands"
    exit 1
fi

TOKEN=$1
GF_ID=${2:-}
MY_ID=${3:-}

if [ -z "$GF_ID" ]; then
    read -r -p "Telegram user ID for pickup messages (GF): " GF_ID
fi
if [ -z "$MY_ID" ]; then
    read -r -p "Telegram user ID for notifications/admin (you): " MY_ID
fi

if ! [[ "$GF_ID" =~ ^[0-9]+$ ]] || ! [[ "$MY_ID" =~ ^[0-9]+$ ]]; then
    _error "User IDs must be numeric."
    exit 1
fi

echo -e "  ${BOLD}Configuration:${NC}"
echo -e "    ${CYAN}GF User ID:${NC}  $GF_ID"
echo -e "    ${CYAN}My User ID:${NC}  $MY_ID"
echo -e ""

# Run the service as this user, not root.
RUN_USER=${SUDO_USER:-$(id -un)}
APP_DIR=$(pwd)

_step "Updating package index" sudo apt update
_step "Installing system dependencies (python3, pip, venv)" sudo apt install -y python3 python3-pip python3-venv

_step "Creating virtual environment" python3 -m venv venv
# shellcheck source=/dev/null
source venv/bin/activate

_step "Installing Python packages" pip install -r requirements.txt

_step "Writing systemd service file" sudo tee /etc/systemd/system/varden-bot.service <<EOF
[Unit]
Description=Varden Telegram Bot
After=network.target

[Service]
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/venv/bin/python3 bot.py
Environment=TELEGRAM_BOT_TOKEN=$TOKEN
Environment=GF_USER_ID=$GF_ID
Environment=MY_USER_ID=$MY_ID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

_step "Restricting service file permissions" sudo chmod 600 /etc/systemd/system/varden-bot.service
_step "Reloading systemd" sudo systemctl daemon-reload
_step "Enabling service" sudo systemctl enable varden-bot
_step "Starting service" sudo systemctl restart varden-bot

_success "Varden Bot installed and running!"
echo ""
echo -e "  ${BOLD}Quick commands:${NC}"
echo -e "    ${CYAN}Status:${NC}  systemctl status varden-bot"
echo -e "    ${CYAN}Logs:${NC}    journalctl -u varden-bot -f"
echo -e "    ${CYAN}Restart:${NC} sudo systemctl restart varden-bot"
echo ""
