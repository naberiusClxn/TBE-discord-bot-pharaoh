import sqlite3

def create_tables(db_path="database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS punishments (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, guild_id TEXT, type TEXT, reason TEXT, expires_at INTEGER, created_at INTEGER DEFAULT (strftime('%s','now')))")
    conn.commit()
    conn.close()
