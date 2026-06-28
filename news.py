import feedparser
import asyncio
import html
import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

RSS_FEEDS = {
    "Void Linux": "https://voidlinux.org/atom.xml",
    "Phoronix": "https://www.phoronix.com/rss.php",
    "Linux Journal": "https://www.linuxjournal.com/feed",
    "Tom's Hardware": "https://www.tomshardware.com/feeds/all",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
}

def _strip_html(text: str) -> str:
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", "", text)

async def _fetch_feed(name: str, url: str) -> list[tuple[str, str, str, str]]:
    try:
        feed = await asyncio.to_thread(feedparser.parse, url)
        results = []
        for entry in feed.entries[:3]:
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            summary = _strip_html(entry.get("summary", ""))
            results.append((name, title, summary, link))
        return results
    except Exception as e:
        logger.warning(f"Error fetching {name}: {e}")
        return []

async def fetch_news() -> str:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    header = f"📰 Linux & Hardware News - {today}\n\n"
    
    all_results = await asyncio.gather(*[_fetch_feed(name, url) for name, url in RSS_FEEDS.items()])
    items = [item for group in all_results for item in group]
    
    if not items:
        return header + "No news available today."
    
    message = header
    for i, (source, title, summary, link) in enumerate(items, 1):
        message += f"{i}. [{source}] {title}\n"
        if len(summary) > 200:
            message += f"{summary[:200]}...\n"
        else:
            message += f"{summary}\n"
        message += f"🔗 {link}\n\n"
    
    return message[:4000]

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(asyncio.run(fetch_news()))
