import disnake
from disnake.ext import commands, tasks
import sqlite3

class VoicePointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.create_table()
        self.voice_points_loop.start()

    def cog_unload(self):
        self.voice_points_loop.cancel()

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS balances (user_id TEXT, guild_id TEXT, balance INTEGER DEFAULT 0)"
        )
        conn.commit()
        conn.close()

    @tasks.loop(seconds=3600)
    async def voice_points_loop(self):
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.bot:
                        continue
                    self.add_points(member, guild)

    @voice_points_loop.before_loop
    async def before_voice_points_loop(self):
        await self.bot.wait_until_ready()

    def add_points(self, member: disnake.Member, guild: disnake.Guild):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance FROM balances WHERE user_id = ? AND guild_id = ?",
            (str(member.id), str(guild.id))
        )
        result = cursor.fetchone()
        if result:
            cursor.execute(
                "UPDATE balances SET balance = balance + 1 WHERE user_id = ? AND guild_id = ?",
                (str(member.id), str(guild.id))
            )
        else:
            cursor.execute(
                "INSERT INTO balances (user_id, guild_id, balance) VALUES (?, ?, ?)",
                (str(member.id), str(guild.id), 1)
            )
        conn.commit()
        conn.close()

def setup(bot):
    bot.add_cog(VoicePointsCog(bot))
