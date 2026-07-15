"""
News Feed Module
================

Fetches the latest Linux and hardware news from configured RSS/Atom feeds,
formats them into an HTML digest suitable for Telegram, and returns the result
as a single string.

Public API:
    fetch_news() — async, returns a formatted news digest string.

Feed sources are defined in ``RSS_FEEDS``.  Each feed is fetched concurrently
via ``asyncio.gather`` so a slow or down feed does not block the others.
"""

import feedparser
import asyncio
import html
import re
import logging
import requests
from io import BytesIO
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Timeout in seconds for fetching a single feed.
_FEED_TIMEOUT = 10

# Total timeout for all feeds combined.
_TOTAL_TIMEOUT = 30

# ---------------------------------------------------------------------------
# Feed configuration
# ---------------------------------------------------------------------------

RSS_FEEDS: dict[str, str] = {
    "Phoronix": "https://www.phoronix.com/rss.php",
    "OMG! Ubuntu": "https://www.omgubuntu.co.uk/feed",
    "Tom's Hardware": "https://www.tomshardware.com/feeds.xml",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
}

# Maximum number of entries to pull from each feed.
_MAX_ENTRIES_PER_FEED = 3

# Skip entries older than this many days.
_MAX_AGE_DAYS = 7

# Telegram message length limit (with a small safety margin).
_MAX_MESSAGE_LENGTH = 4090

# Summaries longer than this are truncated with an ellipsis.
_SUMMARY_CHAR_LIMIT = 180

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_html(text: str) -> str:
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", "", text)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _fetch_feed_sync(name: str, url: str) -> list[tuple[str, str, str, str]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=_MAX_AGE_DAYS)

    resp = requests.get(url, timeout=_FEED_TIMEOUT, headers={
        "User-Agent": "VardenBot/1.0 (+https://github.com/TueDej/varden-bot)"
    })
    resp.raise_for_status()

    feed = feedparser.parse(BytesIO(resp.content))

    results = []
    for entry in feed.entries:
        if len(results) >= _MAX_ENTRIES_PER_FEED:
            break

        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        if pub:
            from time import mktime
            entry_date = datetime.fromtimestamp(mktime(pub), tz=timezone.utc)
            if entry_date < cutoff:
                continue

        title = entry.get("title", "No title")
        link = entry.get("link", "")
        summary = _strip_html(entry.get("summary", ""))
        results.append((name, title, summary, link))
    return results


async def _fetch_feed(name: str, url: str) -> list[tuple[str, str, str, str]]:
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_fetch_feed_sync, name, url),
            timeout=_FEED_TIMEOUT + 5,
        )
    except Exception as e:
        logger.warning("Error fetching %s: %s", name, e)
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_news() -> str:
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    header = f"📰 <b>Linux & Hardware News</b>\n📅 {today}\n\n"

    try:
        all_results = await asyncio.wait_for(
            asyncio.gather(
                *[_fetch_feed(name, url) for name, url in RSS_FEEDS.items()]
            ),
            timeout=_TOTAL_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.warning("News fetch timed out after %ds", _TOTAL_TIMEOUT)
        return header + "News fetch timed out. Try again later."

    groups = [
        (name, results) for (name, _), results in zip(RSS_FEEDS.items(), all_results)
        if results
    ]

    if not groups:
        return header + "No news available today."

    message = header
    for source, results in groups:
        message += f"<b>__________ {_escape_html(source)} __________</b>\n"
        for i, (_src, title, summary, link) in enumerate(results, 1):
            title_h = _escape_html(title)
            summary_h = _escape_html(
                summary[:_SUMMARY_CHAR_LIMIT] + ("…" if len(summary) > _SUMMARY_CHAR_LIMIT else "")
            )
            message += (
                f"<b>{i}.</b> {title_h}\n"
                f"{summary_h}\n"
                f"<a href=\"{link}\">🔗 Link</a>\n\n"
            )

    return message[:_MAX_MESSAGE_LENGTH]


# ---------------------------------------------------------------------------
# Standalone test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(asyncio.run(fetch_news()))
