import sqlite3
from datetime import datetime, timedelta

DB_NAME = "bot.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                until TIMESTAMP
            )
        """)
        conn.commit()

def save_request(user_id, username):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO requests (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()

def get_stats_summary():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM requests")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT user_id) FROM requests")
        users = c.fetchone()[0]
        return f"Всего запросов: {total}\nУникальных пользователей: {users}"

def is_subscribed(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT until FROM subscriptions WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return datetime.fromisoformat(row[0]) > datetime.now()
        return False

def add_subscription(user_id, days=30):
    until = datetime.now() + timedelta(days=days)
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("REPLACE INTO subscriptions (user_id, until) VALUES (?, ?)", (user_id, until.isoformat()))
        conn.commit()
