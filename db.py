import sqlite3
from datetime import datetime

DB_PATH = "stats.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_request(user_id, username):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO requests (user_id, username, timestamp)
        VALUES (?, ?, ?)
    ''', (user_id, username, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_stats_summary():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM requests")
    total = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(username, 'unknown') AS user, COUNT(*) AS c 
        FROM requests 
        GROUP BY user 
        ORDER BY c DESC 
        LIMIT 5
    """)
    top_users = cursor.fetchall()
    conn.close()

    summary = f"📊 Всего запросов: {total}\n\n👤 Топ пользователей:\n"
    for username, count in top_users:
        summary += f"@{username}: {count}\n"

    return summary
