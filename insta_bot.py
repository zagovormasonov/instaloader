import os
import logging
import yt_dlp
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from fastapi import FastAPI, Request
import nest_asyncio

nest_asyncio.apply()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота и адрес вебхука (лучше вынести в .env, но пока в коде)
TOKEN = "478113079:AAHcNPFtEfpn6O-i52fSvGOTeJgntu2ZgdA"
WEBHOOK_URL = "https://instaloader-g43c.onrender.com/webhook"

# Создаём FastAPI и Telegram приложение
app = FastAPI()
telegram_app = ApplicationBuilder().token(TOKEN).build()


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли ссылку на Instagram-видео.")

telegram_app.add_handler(CommandHandler("start", start))


# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "instagram.com" not in text:
        await update.message.reply_text("Пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("Скачиваю видео, подожди...")

    try:
        file_path = download_instagram_video(text)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
    except Exception as e:
        logger.error(f"Ошибка при скачивании видео: {e}")
        await update.message.reply_text(f"Ошибка: {e}")

telegram_app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))


# Загрузка Instagram-видео
def download_instagram_video(instagram_url):
    output_path = "video.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'cookies': 'cookies.txt',  # если нужно пройти авторизацию
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(instagram_url, download=True)
        return ydl.prepare_filename(info)


# Webhook-эндпоинт
@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = Update.de_json(await request.json(), telegram_app.bot)
        await telegram_app.update_queue.put(update)
    except Exception as e:
        logger.error(f"Ошибка обработки вебхука: {e}")
    return {"ok": True}


# Эндпоинт для проверки работоспособности
@app.get("/health")
async def health():
    return {"status": "ok"}


# Установка вебхука при запуске
@app.on_event("startup")
async def on_startup():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    logger.info(f"Webhook установлен: {WEBHOOK_URL}")


# Удаление вебхука при завершении
@app.on_event("shutdown")
async def on_shutdown():
    await telegram_app.bot.delete_webhook()
    logger.info("Webhook удалён")
