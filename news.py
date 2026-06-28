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
    header = f"\U0001f4f0 Linux & Hardware News - {today}\n\n"
    
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
        message += f"\U0001f517 {link}\n\n"
    
    return message[:4000]

if __name__ == "__main__":
    print(asyncio.run(fetch_news()))
