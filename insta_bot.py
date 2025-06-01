import os
import yt_dlp
import asyncio
import nest_asyncio
import sqlite3

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

from db import init_db, save_request, get_stats_summary, is_paid_user, save_paid_user

nest_asyncio.apply()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Укажи свой Telegram ID
COOKIES_PATH = "cookies.txt"
TON_ADDRESS = "UQA7dn_RUi7WF2E2-gqhK4pmc2n4cx6yEqCb_M-Vn50gxU9s"  # Замените на ваш адрес

# Инициализация базы
init_db()

# Скачать видео
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

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли ссылку на Instagram-видео или напиши /pay для подписки.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.username or "unknown"

    if not is_paid_user(user.id):
        await update.message.reply_text("❗️Для доступа к боту нужно оформить подписку: /pay")
        return

    text = update.message.text

    if "instagram.com" not in text:
        await update.message.reply_text("Пришли ссылку на Instagram-видео.")
        return

    await update.message.reply_text("⏬ Скачиваю видео...")

    try:
        file_path = download_instagram_video(text)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
        save_request(user.id, username)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return

    summary = get_stats_summary()
    await update.message.reply_text(summary)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ton_link = f"https://tonkeeper.com/transfer/{TON_ADDRESS}?amount=2&text=Подписка+на+бота"

    keyboard = [[InlineKeyboardButton("Оплатить через Tonkeeper 💎", url=ton_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "💰 Для доступа к боту оплатите 2 TON по кнопке ниже. После оплаты напишите сюда, чтобы мы проверили транзакцию:",
        reply_markup=reply_markup
    )

# Запуск
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🤖 Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

