import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from news import fetch_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_ids = set()

TEHRAN_OFFSET = timedelta(hours=3, minutes=30)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)
    await update.message.reply_text(update.message.text)

async def pull(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching news...")
    news = await fetch_news()
    await update.message.reply_text(news)

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
                    await bot.send_message(chat_id=chat_id, text=news)
                except Exception as e:
                    logger.error(f"Failed to send to {chat_id}: {e}")
                    chat_ids.discard(chat_id)
        except Exception as e:
            logger.error(f"Error fetching news: {e}")

async def post_init(application):
    asyncio.create_task(daily_news(application.bot))

def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("pull", pull))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot started")
    app.run_polling()

if __name__ == '__main__':
    main()
