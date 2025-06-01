import os
import yt_dlp
import asyncio
import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from db import init_db, save_request, get_stats_summary

# Логирование
logging.basicConfig(level=logging.INFO)

# Обход ограничений event loop в Render
nest_asyncio.apply()

# Токен и ID админа
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Подставь свой ID

# Файл cookies
COOKIES_PATH = "cookies.txt"

# Инициализация БД
init_db()

# Загрузка и скачивание видео
def download_instagram_video(instagram_url):
    output_path = "video.%(ext)s"
    ydl_opts = {
        'outtmpl': output_path,
        'format': 'best[ext=mp4]',
        'quiet': True,
        'cookies': COOKIES_PATH,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(instagram_url, download=True)
        return ydl.prepare_filename(info)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Поддержать проект ❤️", url="https://t.me/your_donation_channel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! Пришли ссылку на Instagram-видео, и я его скачаю.",
        reply_markup=reply_markup
    )

# Обработка текста
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    username = user.username or "unknown"

    if "instagram.com" not in text:
        await update.message.reply_text("Пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("⏳ Скачиваю видео, подожди...")

    try:
        file_path = download_instagram_video(text)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
        save_request(user.id, username)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# Команда /stats
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return

    summary = get_stats_summary()
    await update.message.reply_text(summary)

# Обработка кнопок
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Спасибо за поддержку! ❤️")

# Главная функция
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))

    print("Бот запущен ✅")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
