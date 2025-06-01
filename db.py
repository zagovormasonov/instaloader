import sqlite3
from datetime import datetime

DB_PATH = "stats.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            timestamp TEXT,
            url TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_request(user_id, username, url):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO requests (user_id, username, timestamp, url)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, datetime.now().isoformat(), url))
    conn.commit()
    conn.close()
