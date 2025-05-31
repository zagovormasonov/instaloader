import os
import yt_dlp
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import asyncio
import nest_asyncio

nest_asyncio.apply()

TOKEN = "478113079:AAHcNPFtEfpn6O-i52fSvGOTeJgntu2ZgdA"  # ← Замени на свой

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли ссылку на Instagram-видео.")

# Обработка сообщений с ссылкой
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "instagram.com" not in text:
        await update.message.reply_text("Пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("Скачиваю видео, подожди...")

    try:
        file_path = download_instagram_video(text)
        with open(file_path, 'rb') as video:
            await update.message.reply_video(video=video)
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

# Скачивание видео через yt-dlp
def download_instagram_video(instagram_url):
    output_path = "video.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'cookies': 'cookies.txt',  # опционально
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(instagram_url, download=True)
        return ydl.prepare_filename(info)

# Основной запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен.")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
