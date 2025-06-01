import os
import yt_dlp
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)
import asyncio
import nest_asyncio
from datetime import datetime, timedelta

nest_asyncio.apply()

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))
COOKIES_PATH = "cookies.txt"
TON_ADDRESS = "UQA7dn_RUi7WF2E2-gqhK4pmc2n4cx6yEqCb_M-Vn50gxU9s"
DB_PATH = "users.db"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  last_request TIMESTAMP,
                  subscribed_until TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_request(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, last_request) VALUES (?, ?, ?)", (user_id, username, now))
    c.execute("UPDATE users SET last_request = ? WHERE user_id = ?", (now, user_id))
    conn.commit()
    conn.close()

def is_subscribed(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT subscribed_until FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    if row and row[0]:
        until = datetime.fromisoformat(row[0])
        return until > datetime.utcnow()
    return False

def add_subscription(user_id, days=30):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.utcnow()
    until = now + timedelta(days=days)
    c.execute("UPDATE users SET subscribed_until = ? WHERE user_id = ?", (until.isoformat(), user_id))
    conn.commit()
    conn.close()

def get_stats_summary():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE subscribed_until > ?", (datetime.utcnow().isoformat(),))
    subs = c.fetchone()[0]
    conn.close()
    return f"👥 Пользователей: {users}\n✅ Подписок активно: {subs}"

# Загрузка видео
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

# Обработчики Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Пришли ссылку на Instagram-видео.\n\n"
        "Чтобы пользоваться ботом, нужно оформить подписку. Используй команду /subscribe"
    )

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ton_url = f"https://tonkeeper.com/transfer/{TON_ADDRESS}?amount=1000000000&text=Подписка+от+{user.id}"

    keyboard = [
        [InlineKeyboardButton("Оплатить 1 TON", url=ton_url)],
        [InlineKeyboardButton("Я оплатил", callback_data="paid")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("💳 Для подписки нажми кнопку ниже и оплати 1 TON:", reply_markup=reply_markup)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "paid":
        user_id = query.from_user.id
        username = query.from_user.username or "unknown"
        save_request(user_id, username)
        add_subscription(user_id)
        await query.edit_message_text("✅ Спасибо! Подписка активирована на 30 дней.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = update.effective_user
    user_id = user.id
    username = user.username or "unknown"

    if "instagram.com" not in text:
        await update.message.reply_text("Пришли ссылку на Instagram-видео.")
        return

    if not is_subscribed(user_id):
        await update.message.reply_text("🚫 У вас нет активной подписки. Используйте /subscribe для её активации.")
        return

    await update.message.reply_text("Скачиваю видео, подожди...")

    try:
        file_path = download_instagram_video(text)
        await update.message.reply_video(video=open(file_path, 'rb'))
        os.remove(file_path)
        save_request(user_id, username)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔️ Доступ запрещён.")
        return

    summary = get_stats_summary()
    await update.message.reply_text(summary)

# Основной запуск
async def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.StatusUpdate.CALLBACK_QUERY, button_callback))
    app.add_handler(MessageHandler(filters.ALL, lambda u, c: None))  # заглушка

    print("Бот запущен")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
