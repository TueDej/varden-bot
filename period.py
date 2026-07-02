import json
import os
import logging
from datetime import datetime, timedelta

PERIODS_DIR = "periods"
PERIODS_FILE = os.path.join(PERIODS_DIR, "periods.json")
SYMPTOMS_DIR = os.path.join(PERIODS_DIR, "symptoms")

logger = logging.getLogger(__name__)

SYMPTOM_OPTIONS = [
    "درد شکم/کمر 😣",
    "خستگی 😴",
    "بیحوالی 😐",
    "خشم 😠",
    "غم/افسردگی 😔",
    "میل به شیرین/نمکی 🍫",
    "پف 🎈",
    "سر درد 🤕",
    "مشکل خواب 🌙",
    "بی‌کقراری 😰",
]

# Generate stable callback IDs for symptoms
SYMBOL_MAP = {
    "درد شکم/کمر 😣": "pain",
    "خستگی 😴": "fatigue",
    "بیحوالی 😐": "apathy",
    "خشم 😠": "anger",
    "غم/افسردگی 😔": "sadness",
    "میل به شیرین/نمکی 🍫": "sugar",
    "پف 🎈": "bloating",
    "سر درد 🤕": "headache",
    "مشکل خواب 🌙": "sleep",
    "بی‌کقراری 😰": "anxiety",
}

SYMBOL_TO_OPTION = {v: k for k, v in SYMBOL_MAP.items()}


def save_period(date_str: str) -> None:
    _ensure_periods_dir()
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return

    entries = []
    if os.path.exists(PERIODS_FILE):
        with open(PERIODS_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)

    if date_str not in entries:
        entries.append(date_str)
    entries.sort()

    with open(PERIODS_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def toggle_symptom(date_str: str, symptom: str) -> list[str]:
    _ensure_symptoms_dir()
    path = _symptoms_file(date_str)
    symptoms = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                symptoms = json.load(f)
        except Exception:
            symptoms = []

    if symptom in symptoms:
        symptoms.remove(symptom)
    else:
        symptoms.append(symptom)

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(symptoms, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Failed to save symptoms: %s", e)
        raise

    return symptoms


def get_symptoms(date_str: str) -> list[str]:
    path = _symptoms_file(date_str)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_summary() -> str:
    if not os.path.exists(PERIODS_FILE):
        return "هنوز پریودی ثبت نشده."

    with open(PERIODS_FILE, "r", encoding="utf-8") as f:
        entries = json.load(f)

    if not entries:
        return "هنوز پریودی ثبت نشده."

    last_date_str = entries[-1]
    last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    today = datetime.now().date()
    days_since = (today - last_date).days

    parts = [
        f"آخرین پریود: {last_date_str}",
        f"روزها از آخرین پریود: {days_since}",
    ]

    if len(entries) >= 2:
        diffs = []
        for i in range(1, len(entries)):
            prev = datetime.strptime(entries[i - 1], "%Y-%m-%d").date()
            curr = datetime.strptime(entries[i], "%Y-%m-%d").date()
            diffs.append((curr - prev).days)

        avg_cycle = sum(diffs) / len(diffs)
        parts.append(f"میانگین چرخه: {avg_cycle:.1f} روز")

        next_date = last_date + timedelta(days=round(avg_cycle))
        days_until = (next_date - today).days
        parts.append(f"پریود بعدی تقریبی: {next_date} ({days_until} روز دیگه)")

    return "\n".join(parts)
