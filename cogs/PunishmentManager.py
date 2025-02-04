import disnake
from disnake.ext import commands
import sqlite3
import asyncio
from datetime import datetime

class PunishmentManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.bot.loop.create_task(self.check_expirations())

    async def check_expirations(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            now = int(datetime.utcnow().timestamp())
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_id, guild_id, type FROM punishments WHERE expires_at IS NOT NULL AND expires_at <= ?", (now,))
            rows = cursor.fetchall()
            for row in rows:
                pid, user_id, guild_id, p_type = row
                guild = self.bot.get_guild(int(guild_id))
                if guild:
                    if p_type == "mute":
                        member = guild.get_member(int(user_id))
                        if member:
                            try:
                                await member.edit(timeout=None, reason="Время таймаута истекло")
                            except:
                                pass
                    elif p_type == "ban":
                        try:
                            await guild.unban(disnake.Object(id=int(user_id)), reason="Время бана истекло")
                        except:
                            pass
                cursor.execute("DELETE FROM punishments WHERE id = ?", (pid,))
                conn.commit()
            conn.close()
            await asyncio.sleep(10)

def setup(bot):
    bot.add_cog(PunishmentManager(bot))
    
