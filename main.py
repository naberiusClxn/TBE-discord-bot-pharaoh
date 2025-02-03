import disnake
from disnake.ext import commands
from disnake.ext.commands import CommandSyncFlags
import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

sync_flags = CommandSyncFlags.default()
bot = commands.InteractionBot(intents=intents)

author_icon_path = "images/hammer.png"

def create_db():
    db_path = "database.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS punishments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            type TEXT NOT NULL,
            reason TEXT NOT NULL,
            expires_at INTEGER,
            created_at INTEGER DEFAULT (strftime('%s','now'))
        )
    """)

    conn.commit()
    conn.close()


@bot.event
async def on_ready():
    print(f"{bot.user}")
    create_db()


def load_cogs():
    for dirpath, _, filenames in os.walk("./cogs"):
        for filename in filenames:
            if filename.endswith(".py") and not filename.startswith("_"):
                cog_path = os.path.relpath(os.path.join(dirpath, filename), start=".").replace(os.sep, ".")[:-3]
                try:
                    bot.load_extension(cog_path)
                    print(f"{cog_path}")
                except Exception as e:
                    print(f"{cog_path}: {e}")


if __name__ == "__main__":
    create_db()
    load_cogs()
    bot.run(TOKEN)
