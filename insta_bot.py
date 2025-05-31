import os
import yt_dlp
import asyncio
import nest_asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

nest_asyncio.apply()

TOKEN = "ВАШ_ТОКЕН_ОТ_БОТА"  # <-- Вставь сюда токен своего Telegram-бота

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на Instagram-видео.")

def download_instagram_video(instagram_url):
    output_path = "video.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'cookies': 'cookies.txt',  # Не забудь положить cookies.txt рядом
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(instagram_url, download=True)
        return ydl.prepare_filename(info)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "instagram.com" not in text:
        await update.message.reply_text("Пожалуйста, пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("Скачиваю видео, подожди...")

    try:
        file_path = download_instagram_video(text)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
    except Exception as e:
        await update.message.reply_text(f"Ошибка при скачивании: {e}")

async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
