import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, JobQueue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_ids = set()

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_ids.add(update.effective_chat.id)
    await update.message.reply_text(update.message.text)

async def notify(context: ContextTypes.DEFAULT_TYPE):
    for chat_id in chat_ids.copy():
        try:
            await context.bot.send_message(chat_id=chat_id, text="10 seconds have passed!")
        except Exception as e:
            logger.error(f"Failed to send to {chat_id}: {e}")
            chat_ids.discard(chat_id)

async def post_init(application):
    await application.job_queue.run_repeating(notify, interval=10, first=10)

def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot started")
    app.run_polling()

if __name__ == '__main__':
    main()
