"""
Roasts Module
=============

Provides a single public coroutine that returns a random roast line.

Roasts are kept playful and light-hearted — no personal attacks, slurs, or
mean-spirited content.  Purely for fun among friends.

Public API:
    fetch_random_roast() — async, returns a roast string.
"""

import random
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Roast data
# ---------------------------------------------------------------------------

ROASTS: list[str] = [
    "You're the reason God created the middle finger.",
    "If you were any more inbred, you'd be a sandwich.",
    "You bring everyone a lot of joy… when you leave.",
    "You're like a cloud. When you disappear, it's a beautiful day.",
    "I'd agree with you, but then we'd both be wrong.",
    "You're proof that evolution can go in reverse.",
    "Some drink from the fountain of knowledge; you gargled.",
    "You have the IQ of a houseplant.",
    "I'm jealous of people who don't know you.",
    "You're not stupid; you just have bad luck when thinking.",
    "If you were any brighter, you'd have to be watered twice a week.",
    "You're like a human GPS — always recalculating.",
    "I'd explain it to you, but I left my crayons at home.",
    "You're the punchline to every joke I never told.",
    "If I had a face like yours, I'd sue my parents.",
    "You're like a software update — I don't want to deal with you right now.",
    "You're the reason I prefer animals.",
    "You have your entire life ahead of you… and I wish you'd start living it somewhere else.",
    "I'm not saying you're ugly, but you'd need a blindfold to kiss you.",
    "You're like a period — I want you on a sheet of paper, not in my life.",
]

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_random_roast() -> str:
    """
    Return a random playful roast from the local list.

    Returns
    -------
    str
        A roast string ready to be sent as a Telegram message.
    """
    return random.choice(ROASTS)
