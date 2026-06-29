# Daily Linux News Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use compose:subagent (recommended) or compose:execute to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the 10-second notification loop with a daily news digest that fetches Linux and hardware news from RSS feeds at 6am Tehran time.

**Architecture:** Use `feedparser` to fetch RSS feeds, format messages with headlines and summaries, and send to all users at scheduled time using asyncio scheduler.

**Tech Stack:** Python 3.12, python-telegram-bot 20.0, feedparser 6.0.11

## Global Constraints

- Python 3.12+
- Run at 6am Tehran time (UTC+3:30, so 2:30 UTC)
- RSS sources: Phoronix, Linux Journal, Tom's Hardware, Ars Technica
- Message format: headlines at top, then summaries with links

---

### Task 1: Create news module

**Files:**
- Create: `news.py`
- Modify: `requirements.txt`

**Interfaces:**
- Produces: `async def fetch_news() -> str` - returns formatted news digest

- [ ] **Step 1: Update requirements.txt**

```
python-telegram-bot==20.0
feedparser==6.0.11
```

- [ ] **Step 2: Create news.py**

```python
import feedparser
import asyncio
from datetime import datetime, timezone

RSS_FEEDS = {
    "Phoronix": "https://www.phoronix.com/rss.php",
    "Linux Journal": "https://www.linuxjournal.com/feed",
    "Tom's Hardware": "https://www.tomshardware.com/feeds/all",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
}

async def fetch_news() -> str:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    header = f"📰 Linux & Hardware News - {today}\n\n"
    
    items = []
    for name, url in RSS_FEEDS.items():
        try:
            feed = await asyncio.to_thread(feedparser.parse, url)
            for entry in feed.entries[:3]:
                title = entry.get("title", "No title")
                link = entry.get("link", "")
                summary = entry.get("summary", "")[:200]
                items.append((name, title, summary, link))
        except Exception as e:
            print(f"Error fetching {name}: {e}")
    
    if not items:
        return header + "No news available today."
    
    message = header
    for i, (source, title, summary, link) in enumerate(items, 1):
        message += f"{i}. [{source}] {title}\n"
        message += f"{summary}...\n"
        message += f"🔗 {link}\n\n"
    
    return message[:4000]

if __name__ == "__main__":
    print(asyncio.run(fetch_news()))
```

- [ ] **Step 3: Test news module locally**

Run: `python3 news.py`
Expected: Outputs formatted news digest

- [ ] **Step 4: Commit**

```bash
git add news.py requirements.txt
git commit -m "feat: add news module with RSS feed fetching"
```

---

### Task 2: Update bot.py with scheduler

**Files:**
- Modify: `bot.py`

**Interfaces:**
- Consumes: `fetch_news()` from news.py
- Produces: Daily news digest sent to all users at 6am Tehran time

- [ ] **Step 1: Update bot.py**

```python
import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from news import fetch_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_ids = set()

TEHRAN_OFFSET = timedelta(hours=3, minutes=30)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)
    await update.message.reply_text(update.message.text)

async def daily_news(bot):
    while True:
        now = datetime.now(timezone.utc)
        tehran_now = now + TEHRAN_OFFSET
        
        target = tehran_now.replace(hour=6, minute=0, second=0, microsecond=0)
        if tehran_now >= target:
            target += timedelta(days=1)
        
        target_utc = target - TEHRAN_OFFSET
        wait_seconds = (target_utc - now).total_seconds()
        
        logger.info(f"Next news in {wait_seconds/3600:.1f} hours")
        await asyncio.sleep(wait_seconds)
        
        try:
            news = await fetch_news()
            for chat_id in chat_ids.copy():
                try:
                    await bot.send_message(chat_id=chat_id, text=news)
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")
                    chat_ids.discard(chat_id)
        except Exception as e:
            logger.error(f"Error fetching news: {e}")

async def post_init(application):
    asyncio.create_task(daily_news(application.bot))

def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot started")
    app.run_polling()

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Test bot locally**

Run: `python3 bot.py`
Expected: Bot starts, logs next news time

- [ ] **Step 3: Commit**

```bash
git add bot.py
git commit -m "feat: replace notify loop with daily news scheduler"
```

---

### Task 3: Deploy and verify

**Files:**
- No file changes

**Interfaces:**
- N/A

- [ ] **Step 1: Push to remote**

```bash
git push
```

- [ ] **Step 2: Deploy on VPS**

Run: `./update.sh`
Expected: Bot restarts with new code

- [ ] **Step 3: Verify bot responds to messages**

Send a message to the bot on Telegram.
Expected: Bot echoes back the message

- [ ] **Step 4: Verify news fetch works**

Run: `python3 news.py` on VPS
Expected: Outputs formatted news digest

- [ ] **Step 5: Check logs for scheduler**

Run: `sudo journalctl -u varden-bot -f`
Expected: Logs show "Next news in X hours"
