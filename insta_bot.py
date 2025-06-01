import os
import yt_dlp
import asyncio
import nest_asyncio
import random
import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

nest_asyncio.apply()

TOKEN = os.getenv("BOT_TOKEN")
COOKIES_DIR = "cookies"
MIN_INTERVAL = 30  # секунд между запросами от одного пользователя
last_request_time = {}

def get_random_cookies():
    cookies_files = [
        os.path.join(COOKIES_DIR, f)
        for f in os.listdir(COOKIES_DIR)
        if f.endswith(".txt")
    ]
    return random.choice(cookies_files) if cookies_files else None

def download_instagram_video(instagram_url, user_id):
    output_path = f"{user_id}_{int(time.time())}.%(ext)s"
    cookies_path = get_random_cookies()

    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'quiet': True,
    }

    if cookies_path:
        ydl_opts['cookies'] = cookies_path

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(instagram_url, download=True)
        return ydl.prepare_filename(info)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Привет! Пришли ссылку на Instagram-видео.")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    now = time.time()

    # Антиспам
    if user_id in last_request_time:
        delta = now - last_request_time[user_id]
        if delta < MIN_INTERVAL:
            await update.message.reply_text(f"⏱ Подожди ещё {int(MIN_INTERVAL - delta)} сек.")
            return

    last_request_time[user_id] = now

    if "instagram.com" not in text:
        await update.message.reply_text("Пожалуйста, пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("⏳ Скачиваю видео...")

    try:
        file_path = download_instagram_video(text, user_id)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Бот запущен")
    await app.run_polling()

# Запуск
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())