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
from io import BytesIO
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Timeout in seconds for fetching a single feed.
_FEED_TIMEOUT = 15

# ---------------------------------------------------------------------------
# Feed configuration
# ---------------------------------------------------------------------------

RSS_FEEDS: dict[str, str] = {
    "Void Linux": "https://voidlinux.org/atom.xml",
    "Phoronix": "https://www.phoronix.com/rss.php",
    "OMG! Ubuntu": "https://www.omgubuntu.co.uk/feed",
    "Tom's Hardware": "https://www.tomshardware.com/feeds/all",
    "Ars Technica": "https://feeds.arstechnica.com/arstechnica/index",
}

# Maximum number of entries to pull from each feed.
_MAX_ENTRIES_PER_FEED = 3

# Telegram message length limit (with a small safety margin).
_MAX_MESSAGE_LENGTH = 4090

# Summaries longer than this are truncated with an ellipsis.
_SUMMARY_CHAR_LIMIT = 300

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _strip_html(text: str) -> str:
    """
    Remove HTML tags and decode entities so that summaries are plain text.
    """
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", "", text)


def _escape_html(text: str) -> str:
    """
    Escape characters that Telegram's HTML parser would misinterpret.
    Only ``&``, ``<``, and ``>`` need escaping.
    """
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


async def _fetch_feed(name: str, url: str) -> list[tuple[str, str, str, str]]:
    """
    Parse a single RSS/Atom feed and return up to ``_MAX_ENTRIES_PER_FEED``
    items as ``(source_name, title, summary, link)`` tuples.

    Uses httpx with a timeout to fetch the feed content, then parses it
    with feedparser.  Returns an empty list on any error so that one bad
    feed doesn't break the entire digest.
    """
    try:
        import httpx

        async with httpx.AsyncClient(timeout=_FEED_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        # feedparser expects a file-like object; wrap the raw bytes.
        feed = await asyncio.to_thread(
            feedparser.parse, BytesIO(resp.content)
        )

        results = []
        for entry in feed.entries[:_MAX_ENTRIES_PER_FEED]:
            title = entry.get("title", "No title")
            link = entry.get("link", "")
            summary = _strip_html(entry.get("summary", ""))
            results.append((name, title, summary, link))
        return results
    except Exception as e:
        logger.warning("Error fetching %s: %s", name, e)
        return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_news() -> str:
    """
    Fetch news from all configured RSS feeds concurrently, then format the
    results into an HTML string suitable for ``parse_mode=ParseMode.HTML``.

    Returns
    -------
    str
        A formatted digest beginning with a header line, followed by numbered
        news items.  Truncated to ``_MAX_MESSAGE_LENGTH`` characters to stay
        within Telegram's per-message limit.
    """
    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    header = f"📰 Linux & Hardware News - {today}\n\n"

    # Fetch all feeds concurrently.
    all_results = await asyncio.gather(
        *[_fetch_feed(name, url) for name, url in RSS_FEEDS.items()]
    )

    # Flatten the list of lists into a single list of tuples.
    items = [item for group in all_results for item in group]

    if not items:
        return header + "No news available today."

    # Build the formatted message.
    message = header
    for i, (source, title, summary, link) in enumerate(items, 1):
        # Escape source and title for safe HTML rendering.
        message += (
            f"{i}. <b>[{_escape_html(source)}] {_escape_html(title)}</b>\n"
        )

        # Truncate long summaries.
        if len(summary) > _SUMMARY_CHAR_LIMIT:
            message += f"{summary[:_SUMMARY_CHAR_LIMIT]}...\n"
        else:
            message += f"{summary}\n"

        message += f"🔗 {link}\n\n"

    # Hard-truncate to respect Telegram's message length limit.
    return message[:_MAX_MESSAGE_LENGTH]


# ---------------------------------------------------------------------------
# Standalone test runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(asyncio.run(fetch_news()))
