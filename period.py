import json
import os
import logging
from datetime import datetime, timedelta

PERIODS_DIR = "periods"
PERIODS_FILE = os.path.join(PERIODS_DIR, "periods.json")
SYMPTOMS_DIR = os.path.join(PERIODS_DIR, "symptoms")

logger = logging.getLogger(__name__)

# Stable English IDs paired with display names.  Callback data uses the ID;
# the display name is shown to the user.
SYMPTOM_OPTIONS = [
    ("pain", "درد شکم/کمر 😣"),
    ("fatigue", "خستگی 😴"),
    ("apathy", "بیحوالی 😐"),
    ("anger", "خشم 😠"),
    ("sadness", "غم/افسردگی 😔"),
    ("sugar", "میل به شیرین/نمکی 🍫"),
    ("bloating", "پف 🎈"),
    ("headache", "سر درد 🤕"),
    ("sleep", "مشکل خواب 🌙"),
    ("anxiety", "بی‌کقراری 😰"),
]

SYMPTOM_IDS = {sid: display for sid, display in SYMPTOM_OPTIONS}
SYMPTOM_DISPLAY = {display: sid for sid, display in SYMPTOM_OPTIONS}


def _ensure_periods_dir() -> None:
    os.makedirs(PERIODS_DIR, exist_ok=True)


def _ensure_symptoms_dir() -> None:
    os.makedirs(SYMPTOMS_DIR, exist_ok=True)


def _symptoms_file(date_str: str) -> str:
    safe = date_str.replace("/", "-")
    return os.path.join(SYMPTOMS_DIR, f"{safe}.json")


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
