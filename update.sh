#!/bin/bash
set -e

git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart varden-bot

echo "Updated and restarted!"
echo "Check status: sudo systemctl status varden-bot"
echo "View logs: sudo journalctl -u varden-bot -f"
