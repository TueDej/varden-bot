import os
import asyncio
import logging
import random
import psutil
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from telegram.constants import ParseMode
from news import fetch_news

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_ids = set()
bot_messages = {}

TEHRAN_OFFSET = timedelta(hours=3, minutes=30)

PERSIAN_JOKES = [
    "یارو میره رستوران، میگه آقا چی دارید؟ میگه غذا داریم. میگه خب چی دارید؟ میگه آقا غذا گفتم دیگه!",
    "یارو زنگ میزنه به دوستش، میگه کجایی؟ دوستش میگه خونه. یارو میگه پس چرا درو باز نمیکنی؟ دوستش میگه آقا تو پشت تلفنی!",
    "یارو میره داروخانه، میگه آقا یه چیزی بدید خنکم کنه. میگه برو پشت یخچال وایسا!",
    "یارو میره کتابخونه، میگه آقا کتاب چاپلوسی دارید؟ میگه آقا شما خیلی خوشگلید ولی کتاب نداریم!",
    "یارو به رفیقش میگه دیروز رفتم سینما، فیلم خیلی خوب بود. رفیقش میگه اسمش چی بود؟ یارو میگه نمیدونم، تابلوشو نخوندم!",
    "یارو میره نانوایی، میگه آقا نون تازه دارید؟ میگه آقا نون همیشه تازهست! یارو میگه پس چرا دیشبیش بوی یخچال میده؟",
    "یارو زنگ میزنه به شماره اورژانس، میگه آقا من خیلی گشنمه! میگن آقا اینجا اورژانسه! میگه آره میخوام زنده بمانم!",
    "یارو میره مسجد، میگه آقا چایی دارید؟ میگن آقا اینجا مسجده! میگه آره میخوام خدا رو ببینم چایی بدم!",
    "یارو به دوستش میگه دیروز رفتم ماهواره خریدم. دوستش میگه خوب شد؟ یارو میگه نه، آنتن نداشت!",
    "یارو میره کافی‌نت، میگه آقا اینترنت دارید؟ میگه آره. یارو میگه پس چرا صفحه باز نمیشه؟ میگه آقا شما باید پول بدید!",
    "یارو زنگ میزنه به رفیقش، میگه بیا بیرون بریم گردش. رفیقش میگه الان بارون میاد. یارو میگه خب با چتر میایم!",
    "یارو میره میوه‌فروشی، میگه آقا موز چنده؟ میگه کیلویی پنج هزار. یارو میگه گرونه! میگه آقا برو باغ موز بچین!",
    "یارو به رفیقش میگه دیروز رفتم استخر، خیلی خوش گذشت. رفیقش میگه شنا بلدی؟ یارو میگه نه ولی خیلی غرق شدم!",
    "یارو میره رستوران، میگه آقا سوپ دارید؟ میگه آره. یارو میگه بده بخورم. میگه آقا باید پول بدی! یارو میگه آقا سوپ میخوام نه مشاوره!",
    "یارو زنگ میزنه به دوستش، میگه کجایی؟ دوستش میگه خونه. یارو میگه پس چرا درو باز نمیکنی؟ دوستش میگه آقا تو پشت تلفنی!",
    "یارو میره کتابخونه، میگه آقا کتاب چاپلوسی دارید؟ میگه آقا شما خیلی خوشگلید ولی کتاب نداریم!",
    "یارو میره نانوایی، میگه آقا نون تازه دارید؟ میگه آقا نون همیشه تازهست! یارو میگه پس چرا دیشبیش بوی یخچال میده؟",
    "یارو زنگ میزنه به شماره اورژانس، میگه آقا من خیلی گشنمه! میگن آقا اینجا اورژانسه! میگه آره میخوام زنده بمانم!",
    "یارو میره مسجد، میگه آقا چایی دارید؟ میگن آقا اینجا مسجده! میگه آره میخوام خدا رو ببینم چایی بدم!",
    "یارو به دوستش میگه دیروز رفتم ماهواره خریدم. دوستش میگه خوب شد؟ یارو میگه نه، آنتن نداشت!",
]

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
    
    joke_text = random.choice(PERSIAN_JOKES)
    msg = await update.message.reply_text(joke_text)
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

async def post_init(application):
    asyncio.create_task(daily_news(application.bot))

def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set")
        return
    
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("pull", pull))
    app.add_handler(CommandHandler("btop", btop))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("joke", joke))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot started")
    app.run_polling()

if __name__ == '__main__':
    main()
