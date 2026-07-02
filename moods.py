import json
import os
import logging
from datetime import datetime, timedelta
from collections import Counter

logger = logging.getLogger(__name__)

MOODS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "moods")


def _ensure_dir() -> None:
    os.makedirs(MOODS_DIR, exist_ok=True)


def _today_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _file_path(date_str: str) -> str:
    return os.path.join(MOODS_DIR, f"{date_str}.json")


def save_mood(mood: str) -> None:
    _ensure_dir()
    ts = datetime.now().strftime("%H:%M")
    entry = {"mood": mood, "ts": ts}
    path = _file_path(_today_str())
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error("Failed to save mood: %s", e)
        raise


def get_summary() -> str:
    _ensure_dir()
    date_strs = []
    for i in range(7):
        d = datetime.now() - timedelta(days=i)
        date_strs.append(d.strftime("%Y-%m-%d"))

    counter: Counter = Counter()
    total = 0
    happy_count = 0

    for date_str in date_strs:
        path = _file_path(date_str)
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        mood = entry.get("mood", "")
                        counter[mood] += 1
                        total += 1
                        if mood == "خوشحالم":
                            happy_count += 1
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.error("Failed to read mood file %s: %s", path, e)

    if total == 0:
        return "هیچ خاطره‌ای از ۷ روز گذشته ندارم."

    dominant = counter.most_common(1)[0][0]
    today = date_strs[0]
    today_count = counter.get("خوشحالم", 0)

    parts = [
        f"📅 خلاصه ۷ روز گذشته",
        f"تعداد کل: {total}",
        f"خوشحالم: {happy_count}",
        f"مزیت غالب: {dominant}",
    ]
    if today_count > 0:
        parts.append(f"امروز ({today}) خوشحال بودی {today_count} بار 🇮🇷")
    return "\n".join(parts)
