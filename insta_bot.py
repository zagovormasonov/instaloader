import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters

# 🔐 Вставь сюда токен своего бота
TELEGRAM_BOT_TOKEN = "478113079:AAHcNPFtEfpn6O-i52fSvGOTeJgntu2ZgdA"

# 📥 Загрузка видео через yt-dlp
async def download_instagram_video(url: str, output_path: str = "video.mp4") -> bool:
    try:
        ydl_opts = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return os.path.exists(output_path)
    except Exception as e:
        print(f"Ошибка при загрузке видео: {e}")
        return False

# 📩 Обработка входящих сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "instagram.com" not in url:
        await update.message.reply_text("Пожалуйста, пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("🔄 Загружаю видео, подожди немного...")

    success = await download_instagram_video(url)
    if success:
        await update.message.reply_video(video=open("video.mp4", "rb"))
        os.remove("video.mp4")
    else:
        await update.message.reply_text("Не удалось загрузить видео 😢")

# 🚀 Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Бот запущен.")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    try:
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError:
        # В случае, если event loop уже запущен (например, в Jupyter или IDLE)
        import nest_asyncio
        nest_asyncio.apply()
        asyncio.get_event_loop().run_until_complete(main())

