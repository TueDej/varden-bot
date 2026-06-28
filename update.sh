#!/bin/bash
set -e

git pull
sudo systemctl restart varden-bot

echo "Updated and restarted!"
echo "Check status: sudo systemctl status varden-bot"
echo "View logs: sudo journalctl -u varden-bot -f"
