import os
import yt_dlp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import asyncio
import nest_asyncio
from db import init_db, save_request, get_stats_summary, is_subscribed, add_subscription

nest_asyncio.apply()

# Получаем токен и ID админа из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Укажи свой Telegram ID
COOKIES_PATH = "cookies.txt"

# Инициализация базы данных
init_db()

# Функция для скачивания видео
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
    await update.message.reply_text("👋 Привет! Пришли ссылку на Instagram-видео.")

# Команда /pay — активирует подписку (в реальности здесь будет подтверждение TON-платежа)
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_subscription(user.id)  # ⚠️ Это заглушка. Настоящая активация должна происходить после платежа
    await update.message.reply_text("✅ Подписка активирована на 30 дней!")

# Команда /stats — просмотр статистики (только для админа)
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return

    summary = get_stats_summary()
    await update.message.reply_text(summary)

# Обработка ссылок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    username = user.username or "unknown"

    if "instagram.com" not in text:
        await update.message.reply_text("Пришли ссылку на Instagram-видео.")
        return

    if not is_subscribed(user.id):
        pay_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔒 Оформить подписку", url="https://tonkeeper.com/transfer/EQ...")]  # Укажи свою ссылку
        ])
        await update.message.reply_text(
            "🚫 Доступ ограничен. Оформи подписку, чтобы пользоваться ботом:",
            reply_markup=pay_button
        )
        return

    await update.message.reply_text("⏳ Скачиваю видео, подожди...")

    try:
        file_path = download_instagram_video(text)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
        save_request(user.id, username)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

# Запуск бота
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
