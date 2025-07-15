import disnake
import os
import shutil
import zipfile

from disnake.ext import commands

from config import TRUST_ROLE_ID
from other.db_utils import get_links_by_date

TEMP_DIR = "temp_journal"

class JournalCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="journal", description="Архив ссылок")
    async def journal(self, inter: disnake.ApplicationCommandInteraction):
        if not any(role.id in TRUST_ROLE_ID for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        await inter.response.defer()

        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR, exist_ok=True)

        import sqlite3
        conn = sqlite3.connect("inventory_links.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT date FROM links")
        dates = [row[0] for row in cursor.fetchall()]
        conn.close()

        for date in dates:
            links = get_links_by_date(date)
            file_path = os.path.join(TEMP_DIR, f"{date}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("\n".join(links))

        zip_path = os.path.join(TEMP_DIR, "journal_archive.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_name in os.listdir(TEMP_DIR):
                if file_name.endswith(".txt"):
                    zipf.write(os.path.join(TEMP_DIR, file_name), file_name)

        file = disnake.File(zip_path, filename="journal_archive.zip")
        await inter.edit_original_message(content="Архив:", file=file)

        shutil.rmtree(TEMP_DIR)

def setup(bot):
    bot.add_cog(JournalCog(bot))