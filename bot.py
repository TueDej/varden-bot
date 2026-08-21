"""
Varden Bot — Main Telegram Bot Module
=====================================

This module is the entry point for the Varden Telegram bot. It wires together
all command handlers, scheduled tasks, and message callbacks into a single
async application that polls Telegram for updates.

Responsibilities:
    - Register command handlers (/start, /pull, /btop, /clear, /joke, etc.)
    - Manage persistent keyboard and inline food-order buttons
    - Track per-chat message IDs for the /clear feature
    - Coordinate background schedulers (daily news, pickup lines, cleanup)
    - Route callback queries from inline keyboards

Environment variables:
    TELEGRAM_BOT_TOKEN  — Bot token from BotFather (required)
    GF_USER_ID          — Telegram user ID for scheduled pickup messages (required)
    MY_USER_ID          — Telegram user ID for food-order notifications (required)
"""

import os
import time
import asyncio
import logging
import psutil
from datetime import datetime, timezone, timedelta

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    CommandHandler,
    CallbackQueryHandler,
    filters,
)
from telegram.constants import ParseMode

from news import fetch_news
from jokes import fetch_random_joke
from pickup import fetch_random_pickup_line, fetch_random_compliment

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (from environment)
# ---------------------------------------------------------------------------

def _env_int(name: str) -> int | None:
    """Parse an integer environment variable, returning None if unset."""
    value = os.environ.get(name)
    return int(value) if value else None


TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GF_USER_ID = _env_int("GF_USER_ID")
MY_USER_ID = _env_int("MY_USER_ID")

# ---------------------------------------------------------------------------
# Shared mutable state
# ---------------------------------------------------------------------------

# Maps chat_id → list of bot message IDs sent in that chat.
# Used by /clear to delete bot messages in bulk.
bot_messages: dict[int, list[int]] = {}

# Maximum number of message IDs tracked per chat (oldest are dropped).
_MAX_TRACKED_MESSAGES = 200

# Chats where the bot is waiting for the user to type a custom order,
# mapped to the unix timestamp of when the wait started.
_chats_awaiting_custom_order: dict[int, float] = {}

# How long the bot waits for a custom order before giving up.
_CUSTOM_ORDER_TIMEOUT = 5 * 60


class _AwaitingCustomOrder(filters.MessageFilter):
    """Pass only for chats that recently asked to type a custom order."""

    def filter(self, message):
        started = _chats_awaiting_custom_order.get(message.chat_id)
        if started is None:
            return False
        if time.time() - started > _CUSTOM_ORDER_TIMEOUT:
            del _chats_awaiting_custom_order[message.chat_id]
            return False
        return True


# Tehran is UTC+3:30 with no daylight saving.
TEHRAN_OFFSET = timedelta(hours=3, minutes=30)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _track_message(chat_id: int, message_id: int) -> None:
    """Append *message_id* to the per-chat tracking list, bounded in size."""
    msgs = bot_messages.setdefault(chat_id, [])
    msgs.append(message_id)
    if len(msgs) > _MAX_TRACKED_MESSAGES:
        del msgs[: len(msgs) - _MAX_TRACKED_MESSAGES]


def _tehran_now() -> datetime:
    """Return the current time in Tehran (UTC+3:30)."""
    return datetime.now(timezone.utc) + TEHRAN_OFFSET


def _seconds_until_tehran(target_hour: int, target_minute: int = 0) -> float:
    """
    Calculate how many seconds remain until the next occurrence of
    *target_hour*:*target_minute* in Tehran time.  If that time has already
    passed today, the target is tomorrow.
    """
    now_utc = datetime.now(timezone.utc)
    tehran = _tehran_now()

    target = tehran.replace(
        hour=target_hour, minute=target_minute, second=0, microsecond=0
    )
    if tehran >= target:
        target += timedelta(days=1)

    target_utc = target - TEHRAN_OFFSET
    return (target_utc - now_utc).total_seconds()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message and show the persistent food-order keyboard."""
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("گذا میخاممم!")]],
        resize_keyboard=True,
    )
    if update.effective_user.id == GF_USER_ID:
        await update.message.reply_text("خوش اومدی حنا خانوم!", reply_markup=kb)
    else:
        await update.message.reply_text("خوش اومدی!", reply_markup=kb)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a list of available commands."""
    help_text = (
        "دستورات من:\n\n"
        "/start - شروع و نمایش کیبورد\n"
        "/help - نمایش این پیام\n"
        "/pull - اخبار لینوکس و سخت‌افزار\n"
        "/btop - وضعیت سرور (CPU, RAM, Disk)\n"
        "/joke - یه جوک تصادفی\n"
        "/pickup - یه خط رمانتیک\n"
        "/compliment - یه تعریف قشنگ\n"
        "/tease - یه میو بفرست 🐱\n"
        "/food - سفارش غذا\n"
        "/clear - پاک کردن پیام‌ها"
    )
    await update.message.reply_text(help_text)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo back any plain-text message that isn't a recognised command."""
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text(update.message.text)
    _track_message(chat_id, msg.message_id)


async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a random joke (from JokeAPI or a local Persian fallback list)."""
    chat_id = update.effective_chat.id
    joke_text = await fetch_random_joke()
    msg = await update.message.reply_text(joke_text)
    _track_message(chat_id, msg.message_id)


async def pickup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a random pickup line."""
    chat_id = update.effective_chat.id
    line = await fetch_random_pickup_line()
    msg = await update.message.reply_text(line)
    _track_message(chat_id, msg.message_id)


async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a random compliment."""
    chat_id = update.effective_chat.id
    line = await fetch_random_compliment()
    msg = await update.message.reply_text(line)
    _track_message(chat_id, msg.message_id)


async def tease(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a 'میو' message to the configured GF user."""
    if update.effective_user.id != MY_USER_ID:
        await update.message.reply_text("فقط خودم اجازه دارم میو بفرستم 😼")
        return
    try:
        await context.bot.send_message(chat_id=GF_USER_ID, text="میو")
        await update.message.reply_text("Sent!")
    except Exception as e:
        logger.error("Failed to send tease: %s", e)
        await update.message.reply_text("Failed to send 😿")


async def food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Present an inline keyboard with food choices and set the persistent
    reply keyboard so the user can re-trigger this menu with one tap.
    """
    _chats_awaiting_custom_order.pop(update.effective_chat.id, None)

    keyboard = [
        [InlineKeyboardButton("شوکولات 🍫", callback_data="food_chocolate")],
        [InlineKeyboardButton("جوجه کباب 🍢", callback_data="food_joojeh")],
        [InlineKeyboardButton("یه چی دیگه ✍️", callback_data="food_custom")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    persistent_kb = ReplyKeyboardMarkup(
        [[KeyboardButton("گذا میخاممم!")]],
        resize_keyboard=True,
    )

    await update.message.reply_text("چی چی میخوی؟", reply_markup=reply_markup)
    # Send a zero-width space to attach the persistent keyboard without
    # showing a visible second message.
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="\u200B",
        reply_markup=persistent_kb,
    )


async def handle_food_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Delegate the persistent 'گذا میخاممم!' keyboard button to ``food``."""
    await food(update, context)


async def food_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle inline-keyboard presses for the food order.

    Edits the original message to confirm the order, then forwards the order
    details to ``MY_USER_ID``.
    """
    query = update.callback_query
    await query.answer()

    logger.info("Food callback from user=%s, data=%s", query.from_user, query.data)

    # "یه چی دیگه" — ask the user to type their own order.
    if query.data == "food_custom":
        _chats_awaiting_custom_order[query.message.chat_id] = time.time()
        try:
            await query.edit_message_text("خودت بنویس چی میخوای 👇")
        except Exception:
            pass
        return

    # Map callback data to a display name.
    FOOD_MAP = {
        "food_chocolate": "شوکولات 🍫",
        "food_joojeh": "جوجه کباب 🍢",
    }
    food_name = FOOD_MAP.get(query.data)
    if food_name is None:
        return

    # Edit the message to confirm.  This can fail if the user double-taps
    # the button (message already edited), so we swallow the error.
    try:
        await query.edit_message_text("بیو دم در سفارشت رسید.")
    except Exception:
        pass

    # Build a safe display name — first_name may be None.
    user = query.from_user
    name = user.first_name or user.username or "Someone"
    order_msg = f"New food order!\n\nFrom: {name}\nOrder: {food_name}"
    logger.info("Sending order to %s: %s", MY_USER_ID, order_msg)

    confirm_kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "ثبت شد! ✅",
                    callback_data=f"confirm_{query.message.chat_id}",
                )
            ]
        ]
    )
    try:
        await context.bot.send_message(
            chat_id=MY_USER_ID, text=order_msg, reply_markup=confirm_kb
        )
        logger.info("Order sent successfully")
    except Exception as e:
        logger.error("Failed to send order: %s", e, exc_info=True)


async def handle_custom_order(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Process a user-typed custom food order.

    Triggered when a chat is in ``_chats_awaiting_custom_order``.  Sends a
    confirmation to the user and forwards the order to ``MY_USER_ID``.
    """
    chat_id = update.effective_chat.id
    _chats_awaiting_custom_order.pop(chat_id, None)

    custom_text = update.message.text

    msg = await update.message.reply_text("بیو دم در سفارشت رسید.")
    _track_message(chat_id, msg.message_id)

    user = update.effective_user
    name = user.first_name or user.username or "Someone"
    order_msg = f"New food order!\n\nFrom: {name}\nOrder: {custom_text}"
    logger.info("Sending custom order to %s: %s", MY_USER_ID, order_msg)

    confirm_kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "ثبت شد! ✅",
                    callback_data=f"confirm_{chat_id}",
                )
            ]
        ]
    )
    try:
        await context.bot.send_message(
            chat_id=MY_USER_ID, text=order_msg, reply_markup=confirm_kb
        )
    except Exception as e:
        logger.error("Failed to send custom order: %s", e, exc_info=True)


async def confirm_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handle the 'ثبت شد!' button on order messages sent to MY_USER_ID.

    Notifies the original user that their order has been confirmed, then
    removes the button so it can't be clicked twice.
    """
    query = update.callback_query
    await query.answer()

    chat_id_str = query.data.removeprefix("confirm_")
    try:
        chat_id_int = int(chat_id_str)
    except ValueError:
        return

    try:
        await context.bot.send_message(
            chat_id=chat_id_int,
            text="اوستا سفارش رو ثبت کرد. باقی‌ش دیگه دست خداس.",
        )
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception as e:
        logger.error("Failed to confirm order: %s", e, exc_info=True)


async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch the latest Linux / hardware news digest and send it."""
    chat_id = update.effective_chat.id

    status = await update.message.reply_text("Fetching news...")
    _track_message(chat_id, status.message_id)

    news = await fetch_news()
    msg = await update.message.reply_text(news, parse_mode=ParseMode.HTML)
    _track_message(chat_id, msg.message_id)


async def btop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Display current server statistics (CPU, RAM, disk, uptime)."""
    if update.effective_user.id != MY_USER_ID:
        await update.message.reply_text("این دستور فقط مال خودمه 😼")
        return

    cpu = await asyncio.to_thread(psutil.cpu_percent, 1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    # Human-readable memory and disk sizes.
    ram_used_mb = mem.used // (1024 ** 2)
    ram_total_mb = mem.total // (1024 ** 2)
    disk_used_gb = disk.used // (1024 ** 3)
    disk_total_gb = disk.total // (1024 ** 3)

    msg = (
        f"<b>📊 Server Stats</b>\n\n"
        f"<b>CPU:</b> {cpu}%\n"
        f"<b>RAM:</b> {mem.percent}% ({ram_used_mb}MB / {ram_total_mb}MB)\n"
        f"<b>Disk:</b> {disk.percent}% ({disk_used_gb}GB / {disk_total_gb}GB)\n"
        f"<b>Uptime:</b> {str(uptime).split('.')[0]}"
    )

    chat_id = update.effective_chat.id
    reply = await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    _track_message(chat_id, reply.message_id)


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Delete the user's command message, all tracked bot messages in this chat,
    and a temporary confirmation.
    """
    chat_id = update.effective_chat.id

    # Attempt to delete the user's /clear command itself.
    try:
        await update.message.delete()
    except Exception:
        pass

    # Delete every tracked bot message in this chat.
    if chat_id in bot_messages:
        for msg_id in bot_messages[chat_id]:
            try:
                await context.bot.delete_message(
                    chat_id=chat_id, message_id=msg_id
                )
            except Exception:
                pass
        bot_messages[chat_id] = []

    # Show a brief confirmation that self-destructs after 2 seconds.
    status = await update.message.reply_text("🧹 Chat cleared")
    await asyncio.sleep(2)
    try:
        await status.delete()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Scheduled background tasks
# ---------------------------------------------------------------------------


async def daily_news(bot) -> None:
    """
    Infinite loop that sends a Linux / hardware news digest to MY_USER_ID
    once per day at 06:00 Tehran time.
    """
    while True:
        wait_seconds = _seconds_until_tehran(target_hour=6)
        logger.info("Next news in %.1f hours", wait_seconds / 3600)
        await asyncio.sleep(wait_seconds)

        try:
            news = await fetch_news()
            await bot.send_message(
                chat_id=MY_USER_ID,
                text=news,
                parse_mode=ParseMode.HTML,
            )
            logger.info("Daily news sent to %s", MY_USER_ID)
        except Exception as e:
            logger.error("Failed to send daily news to %s: %s", MY_USER_ID, e)


async def scheduled_pickups(bot) -> None:
    """
    Infinite loop that sends a pickup line followed by a compliment to the
    configured GF user at 09:00 and 21:00 Tehran time.
    """
    SCHEDULE_HOURS = [9, 21]

    while True:
        # Find the next scheduled hour that hasn't passed yet today.
        tehran = _tehran_now()
        next_hour = None
        for hour in SCHEDULE_HOURS:
            if tehran.hour < hour:
                next_hour = hour
                break

        # If all scheduled hours have passed, target tomorrow's first slot.
        if next_hour is None:
            next_hour = SCHEDULE_HOURS[0]

        wait_seconds = _seconds_until_tehran(target_hour=next_hour)
        logger.info("Next pickup in %.1f hours", wait_seconds / 3600)
        await asyncio.sleep(wait_seconds)

        try:
            line = await fetch_random_pickup_line()
            await bot.send_message(
                chat_id=GF_USER_ID, text=line
            )

            # Wait one minute between the pickup line and the compliment
            # so the two messages feel like separate thoughts.
            await asyncio.sleep(60)

            compliment_text = await fetch_random_compliment()
            await bot.send_message(chat_id=GF_USER_ID, text=compliment_text)
        except Exception as e:
            logger.error("Error sending pickup: %s", e)


async def cleanup_stale() -> None:
    """
    Hourly housekeeping — expire stale custom-order waits and purge empty
    message lists to keep memory bounded.
    """
    while True:
        await asyncio.sleep(3600)

        # Expire custom-order waits older than the timeout.
        now = time.time()
        expired = [
            cid
            for cid, started in _chats_awaiting_custom_order.items()
            if now - started > _CUSTOM_ORDER_TIMEOUT
        ]
        for cid in expired:
            del _chats_awaiting_custom_order[cid]

        # Remove empty message lists.
        empty_chats = [cid for cid, msgs in bot_messages.items() if not msgs]
        for cid in empty_chats:
            del bot_messages[cid]


# ---------------------------------------------------------------------------
# Application lifecycle
# ---------------------------------------------------------------------------


# Keep references to background tasks so they aren't garbage-collected.
_background_tasks: list[asyncio.Task] = []


async def post_init(application) -> None:
    """Called after the Application object is built — launch background tasks."""
    _background_tasks.extend(
        [
            asyncio.create_task(daily_news(application.bot)),
            asyncio.create_task(scheduled_pickups(application.bot)),
            asyncio.create_task(cleanup_stale()),
        ]
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Build the bot application, register all handlers, and start polling."""
    missing = [
        name
        for name in ("TELEGRAM_BOT_TOKEN", "GF_USER_ID", "MY_USER_ID")
        if not os.environ.get(name)
    ]
    if missing:
        logger.error(
            "Missing required environment variables: %s", ", ".join(missing)
        )
        return

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Command handlers — order matters: more specific patterns first.
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("pull", pull))
    app.add_handler(CommandHandler("btop", btop))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("pickup", pickup))
    app.add_handler(CommandHandler("compliment", compliment))
    app.add_handler(CommandHandler("tease", tease))
    app.add_handler(CommandHandler("food", food))

    # Inline keyboard callback for food orders.
    app.add_handler(CallbackQueryHandler(food_callback, pattern="^food_"))

    # Inline keyboard callback for order confirmation ("ثبت شد!").
    app.add_handler(CallbackQueryHandler(confirm_callback, pattern="^confirm_"))

    # Persistent keyboard button → delegate to food handler.
    app.add_handler(
        MessageHandler(filters.Text(["گذا میخاممم!"]), handle_food_button)
    )

    # Custom food order text input (must be before echo catch-all).
    app.add_handler(
        MessageHandler(
            _AwaitingCustomOrder() & ~filters.COMMAND, handle_custom_order
        )
    )

    # Catch-all for plain text (must be last).
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
