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
    "I was going to wait to tell you how amazing you are, but I didn't want to keep it to myself another second.",
    "I'm not a photographer but I can definitely picture us together.",
    "You make even the most ordinary days feel special.",
    "Whenever you smile, the rest of the world just fades away.",
    "You must be tired — you've been running through my mind all day.",
    "You have this way of making everything brighter just by being near.",
    "I dropped something. My jaw.",
    "I didn't know what perfect was until I met you.",
    "I must be a snowflake because I've fallen for you.",
    "You look great, but you're even better when you laugh.",
    "I'm planning our future before you even say yes.",
    "Do you have a map? Because I keep getting lost in you.",
    "You're exactly as beautiful in real life as you look when I close my eyes.",
    "They say nothing is forever, but I want whatever we have to be.",
    "I don't need directions — every road with you looks right.",
    "I've got a feeling we could be something really good.",
    "Is your smile contagious? Because I caught it and I never want to recover.",
    "I'd say God bless you, but it looks like he already did.",
    "You're the kind of person that makes me want to be the best version of myself.",
    "I don't have to daydream about you — I'm already there.",
]

COMPLIMENTS: list[str] = [
    "That smile of yours could honestly change anyone's day.",
    "You radiate a warmth I can't put into words.",
    "You are effortlessly yourself, and it is honestly my favorite thing about you.",
    "The way you care about people says everything about who you are.",
    "You make everything better just by being near.",
    "You are so much more beautiful than you realize.",
    "Your laugh is my favorite sound in the world.",
    "You have this unshakable glow — even on the hardest days.",
    "I love the way your eyes light up when you talk about what matters to you.",
    "You make the ordinary feel like something worth celebrating.",
    "You're simply unforgettable.",
    "No matter what anyone says, you are absolutely incredible.",
    "You make the good moments even better and the hard ones easier.",
    "I don't know how I got this lucky, but I'm so glad I did.",
    "I'd be lying if I said your pictures did you justice — they really don't.",
    "You have no idea the difference you make just by being you.",
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
