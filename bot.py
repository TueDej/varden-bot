import os
import asyncio
import logging
import psutil
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from telegram.constants import ParseMode
from news import fetch_news
from jokes import fetch_random_joke
from pickup import fetch_random_pickup_line, fetch_random_compliment

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
GF_USER_ID = int(os.environ.get('GF_USER_ID', '190637471'))
chat_ids = set()
bot_messages = {}

TEHRAN_OFFSET = timedelta(hours=3, minutes=30)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)
    msg = await update.message.reply_text(update.message.text)
    chat_id = update.effective_chat.id
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    bot_messages[chat_id].append(msg.message_id)

async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    
    joke_text = await fetch_random_joke()
    msg = await update.message.reply_text(joke_text)
    bot_messages[chat_id].append(msg.message_id)

async def pickup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    
    line = await fetch_random_pickup_line()
    msg = await update.message.reply_text(line)
    bot_messages[chat_id].append(msg.message_id)

async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    
    line = await fetch_random_compliment()
    msg = await update.message.reply_text(line)
    bot_messages[chat_id].append(msg.message_id)

async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    
    status = await update.message.reply_text("Fetching news...")
    bot_messages[chat_id].append(status.message_id)
    
    news = await fetch_news()
    msg = await update.message.reply_text(news, parse_mode=ParseMode.HTML)
    bot_messages[chat_id].append(msg.message_id)

async def btop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
    
    msg = f"""<b>📊 Server Stats</b>

<b>CPU:</b> {cpu}%
<b>RAM:</b> {mem.percent}% ({mem.used // (1024**2)}MB / {mem.total // (1024**2)}MB)
<b>Disk:</b> {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)
<b>Uptime:</b> {str(uptime).split('.')[0]}"""
    
    chat_id = update.effective_chat.id
    if chat_id not in bot_messages:
        bot_messages[chat_id] = []
    
    reply = await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    bot_messages[chat_id].append(reply.message_id)

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    try:
        await update.message.delete()
    except:
        pass
    
    if chat_id in bot_messages:
        for msg_id in bot_messages[chat_id]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
            except:
                pass
        bot_messages[chat_id] = []
    
    status = await update.message.reply_text("🧹 Chat cleared")
    await asyncio.sleep(2)
    try:
        await status.delete()
    except:
        pass

async def daily_news(bot):
    while True:
        now = datetime.now(timezone.utc)
        tehran_now = now + TEHRAN_OFFSET
        
        target = tehran_now.replace(hour=6, minute=0, second=0, microsecond=0)
        if tehran_now >= target:
            target += timedelta(days=1)
        
        target_utc = target - TEHRAN_OFFSET
        wait_seconds = (target_utc - now).total_seconds()
        
        logger.info(f"Next news in {wait_seconds/3600:.1f} hours")
        await asyncio.sleep(wait_seconds)
        
        try:
            news = await fetch_news()
            for chat_id in chat_ids.copy():
                try:
                    msg = await bot.send_message(chat_id=chat_id, text=news, parse_mode=ParseMode.HTML)
                    if chat_id not in bot_messages:
                        bot_messages[chat_id] = []
                    bot_messages[chat_id].append(msg.message_id)
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")
                    chat_ids.discard(chat_id)
        except Exception as e:
            logger.error(f"Error fetching news: {e}")

async def scheduled_pickups(bot):
    SCHEDULE_HOURS = [9, 21]
    
    while True:
        now = datetime.now(timezone.utc)
        tehran_now = now + TEHRAN_OFFSET
        
        next_time = None
        for hour in SCHEDULE_HOURS:
            target = tehran_now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if tehran_now < target:
                next_time = target
                break
        
        if next_time is None:
            target = tehran_now.replace(hour=SCHEDULE_HOURS[0], minute=0, second=0, microsecond=0) + timedelta(days=1)
            next_time = target
        
        target_utc = next_time - TEHRAN_OFFSET
        wait_seconds = (target_utc - now).total_seconds()
        
        logger.info(f"Next pickup in {wait_seconds/3600:.1f} hours")
        await asyncio.sleep(wait_seconds)
        
        try:
            line = await fetch_random_pickup_line()
            await bot.send_message(chat_id=GF_USER_ID, text=f"Hey beautiful! {line}")
            
            await asyncio.sleep(60)
            
            compliment = await fetch_random_compliment()
            await bot.send_message(chat_id=GF_USER_ID, text=compliment)
        except Exception as e:
            logger.error(f"Error sending pickup: {e}")

async def post_init(application):
    asyncio.create_task(daily_news(application.bot))
    asyncio.create_task(scheduled_pickups(application.bot))

def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("pull", pull))
    app.add_handler(CommandHandler("btop", btop))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(CommandHandler("pickup", pickup))
    app.add_handler(CommandHandler("compliment", compliment))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot started")
    app.run_polling()

if __name__ == '__main__':
    main()
