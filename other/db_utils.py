from datetime import datetime
import sqlite3

DB_NAME = "inventory_links.db"

def create_tables(db_path="database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS punishments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, guild_id TEXT, type TEXT, reason TEXT, expires_at INTEGER, created_at INTEGER DEFAULT (strftime('%s','now')))")
    conn.commit()
    conn.close()

def init_database():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            link TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def add_link(link: str):
    today = datetime.now().strftime("day-%d-%m-%Y")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO links (date, link) VALUES (?, ?)", (today, link))
    conn.commit()
    conn.close()

def get_links_by_date(date: str) -> list[str]:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT link FROM links WHERE date = ?", (date,))
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results