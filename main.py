import disnake
from disnake.ext import commands
from disnake.ext.commands import CommandSyncFlags
import os
import sqlite3
from dotenv import load_dotenv

from rent.buttons.RentButtonView import RentButtonView, RentModerationView
from rent.database.database_util import get_all_rent_channels

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = disnake.Intents.default()
intents.members = True
intents.message_content = True

sync_flags = CommandSyncFlags.default()
bot = commands.InteractionBot(intents=intents)

author_icon_path = "images/hammer.png"
author_icon_path_notif = "images/Notification.png"
bat_icon = "images/profile/0Bat.png"
font_path = "fonts/Montserrat.ttf"
banner_path = "images/banner.gif"

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balances (
            user_id TEXT NOT NULL,
            guild_id TEXT NOT NULL,
            balance INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, guild_id)
        )
    """)

    cursor.execute("""
           CREATE TABLE IF NOT EXISTS purchases (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id TEXT NOT NULL,
               guild_id TEXT NOT NULL,
               item_name TEXT NOT NULL,
               cost INTEGER NOT NULL,
               purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
           )
       """)

    conn.commit()
    conn.close()


@bot.event
async def on_ready():
    bot.add_view(RentButtonView())
    for channel_id in get_all_rent_channels():
        bot.add_view(RentModerationView(channel_id))
    print(f"{bot.user}")
    create_db()


def load_cogs():
    for dirpath, _, filenames in os.walk("./cogs"):
        if "__pycache__" in dirpath:
            continue

        for filename in filenames:
            if filename.endswith(".py") and not filename.startswith("_"):
                cog_path = os.path.relpath(os.path.join(dirpath, filename), start=".").replace(os.sep, ".")[:-3]

                if cog_path in bot.extensions:
                    print(f"⚠️ {cog_path} уже загружен, пропускаем")
                    continue

                try:
                    bot.load_extension(cog_path)
                    print(f"✅ {cog_path} загружен")
                except Exception as e:
                    print(f"❌ Ошибка в {cog_path}: {e}")




if __name__ == "__main__":
    create_db()
    load_cogs()
    bot.run(TOKEN)
    