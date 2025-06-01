import os
import time
import yt_dlp
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

from db import init_db, save_request

nest_asyncio.apply()

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")
COOKIES_PATH = "cookies.txt"

# Антиспам: задержка между запросами одного пользователя
MIN_INTERVAL = 10  # секунд
last_request_time = {}

# Функция скачивания видео
def download_instagram_video(instagram_url, user_id):
    output_path = f"video_{user_id}.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'cookies': COOKIES_PATH,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(instagram_url, download=True)
        return ydl.prepare_filename(info)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли ссылку на Instagram-видео, и я его скачаю.")

# Обработчик сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
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

    await update.message.reply_text("⏳ Скачиваю видео, подожди немного...")

    try:
        # Сохраняем статистику
        save_request(user_id, username, text)

        # Скачиваем видео
        file_path = download_instagram_video(text, user_id)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка: {e}")

# Главная функция
async def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен")
    await app.run_polling()

# Запуск
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())