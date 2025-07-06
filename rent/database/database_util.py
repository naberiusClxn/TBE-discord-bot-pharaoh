import sqlite3

conn = sqlite3.connect("rent_requests.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS rent_channels (
    channel_id INTEGER PRIMARY KEY
)
""")
conn.commit()

def add_rent_channel(channel_id: int):
    cursor.execute("INSERT OR IGNORE INTO rent_channels (channel_id) VALUES (?)", (channel_id,))
    conn.commit()

def remove_rent_channel(channel_id: int):
    cursor.execute("DELETE FROM rent_channels WHERE channel_id = ?", (channel_id,))
    conn.commit()

def get_all_rent_channels():
    cursor.execute("SELECT channel_id FROM rent_channels")
    return [row[0] for row in cursor.fetchall()]
