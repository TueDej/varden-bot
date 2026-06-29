"""
Pickup Lines & Compliments Module
==================================

Provides two public coroutines that return random pickup lines or
compliments.

Each function first attempts to fetch from an external web API.  If the
API is unreachable or returns an unexpected format, a curated local list
is used as a fallback.

Public API:
    fetch_random_pickup_line()  — async, returns a pickup line string.
    fetch_random_compliment()   — async, returns a compliment string.
"""

import random
import logging
import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback data — local lists used when APIs are unavailable.
# ---------------------------------------------------------------------------

PICKUP_LINES: list[str] = [
    "Are you a magician? Because whenever I look at you, everyone else disappears.",
    "Do you have a map? Because I just got lost in your eyes.",
    "Are you a parking ticket? Because you've got 'fine' written all over you.",
    "Is your name Wi-Fi? Because I'm really feeling a connection.",
    "Are you a bank loan? Because you've got my interest.",
    "Do you believe in love at first sight, or should I walk by again?",
    "Are you a campfire? Because you're hot and I want s'more.",
    "You must be a light switch, because you just turned me on.",
    "Are you a time traveler? Because I see you in my future.",
    "Do you have a Band-Aid? Because I just scraped my knee falling for you.",
    "Are you a camera? Because every time I look at you, I smile.",
    "Is your dad a boxer? Because you're a knockout.",
    "Are you a snowstorm? Because you make my heart race.",
    "Do you have a sunburn, or are you always this hot?",
    "Are you a cat? Because you're purr-fect.",
    "Are you a dictionary? Because you add meaning to my life.",
    "Is your name Google? Because you have everything I've been searching for.",
    "Are you a loan? Because you've got my interest.",
    "Do you have a name, or can I call you mine?",
    "Are you a volcano? Because I lava you.",
]

COMPLIMENTS: list[str] = [
    "You have the best laugh I've ever heard.",
    "Your eyes are incredible.",
    "You make the world a better place just by being in it.",
    "You have the most amazing smile.",
    "You're even more beautiful on the inside than you are on the outside.",
    "You're one of a kind, and that's the best kind.",
    "Your kindness is contagious.",
    "You make everything more fun.",
    "You're the best thing that's ever happened to me.",
    "You have great taste, obviously — you're talking to me.",
    "You light up every room you walk into.",
    "Your intelligence is incredibly attractive.",
    "You make me want to be a better person.",
    "You're the reason I look at my phone and smile.",
    "You're more amazing than you know.",
    "You have the patience of a saint.",
    "Your creativity blows my mind.",
    "You're the kind of person everyone wants to be around.",
    "You're absolutely stunning.",
    "You make the ordinary extraordinary.",
]

# API endpoints.
_QUOTE_API_URL = "https://api.quotable.io/random?tags=love"
_COMPLIMENT_API_URL = "https://complimentr.com/api"

# HTTP timeout in seconds.
_REQUEST_TIMEOUT = 10

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_random_pickup_line() -> str:
    """
    Return a random pickup line.

    Attempts to fetch from the Quotable API (love-tagged quotes) first.
    On failure, falls back to a random entry from ``PICKUP_LINES``.

    Returns
    -------
    str
        A pickup line string.
    """
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            resp = await client.get(_QUOTE_API_URL)
            if resp.status_code == 200:
                data = resp.json()
                return f'"{data["content"]}"\n— {data["author"]}'
    except Exception as e:
        logger.warning("Quote API failed: %s", e)

    return random.choice(PICKUP_LINES)


async def fetch_random_compliment() -> str:
    """
    Return a random compliment.

    Attempts to fetch from the Complimentr API first.  On failure, falls
    back to a random entry from ``COMPLIMENTS``.

    Returns
    -------
    str
        A compliment string.
    """
    try:
        async with httpx.AsyncClient(timeout=_REQUEST_TIMEOUT) as client:
            resp = await client.get(_COMPLIMENT_API_URL)
            if resp.status_code == 200:
                data = resp.json()
                return data["compliment"]
    except Exception as e:
        logger.warning("Compliment API failed: %s", e)

    return random.choice(COMPLIMENTS)
