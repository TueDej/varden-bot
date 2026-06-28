#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <your-varden-bot-token> [gf-user-id] [my-user-id]"
    exit 1
fi

TOKEN=$1
GF_ID=${2:-190637471}
MY_ID=${3:-2059317327}

sudo apt update && sudo apt install -y python3 python3-pip python3-venv

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

sudo tee /etc/systemd/system/varden-bot.service > /dev/null <<EOF
[Unit]
Description=Telegram Echo Bot
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

sudo systemctl daemon-reload
sudo systemctl enable varden-bot
sudo systemctl start varden-bot

echo "Bot installed and running!"
echo "Check status: sudo systemctl status varden-bot"
echo "View logs: sudo journalctl -u varden-bot -f"
