import sqlite3

def init_db():
    conn = sqlite3.connect("db.sqlite")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS paid_users (
                    user_id INTEGER PRIMARY KEY,
                    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()

def save_request(user_id, username):
    conn = sqlite3.connect("db.sqlite")
    c = conn.cursor()
    c.execute("INSERT INTO requests (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()

def get_stats_summary():
    conn = sqlite3.connect("db.sqlite")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM requests")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM paid_users")
    paid = c.fetchone()[0]
    conn.close()
    return f"Всего запросов: {total}\nПлатных пользователей: {paid}"

def save_paid_user(user_id):
    conn = sqlite3.connect("db.sqlite")
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO paid_users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def is_paid_user(user_id):
    conn = sqlite3.connect("db.sqlite")
    c = conn.cursor()
    c.execute("SELECT 1 FROM paid_users WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    conn.close()
    return result is not None
