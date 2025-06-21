import disnake
from disnake.ext import commands
import asyncio
import sqlite3
from config import channels_voice


class VoicePointsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.create_table()
        self.voice_timers = {}

    def create_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS balances (
                user_id TEXT, 
                guild_id TEXT, 
                balance INTEGER DEFAULT 0,
                voice_hours INTEGER DEFAULT 0
            )
            """
        )
        conn.commit()
        conn.close()

    async def track_voice_time(self, member: disnake.Member, guild: disnake.Guild):
        guild_id = guild.id
        user_id = member.id

        while member.voice and member.voice.channel and member.voice.channel.id in channels_voice:
            await asyncio.sleep(3600)

            if member.voice and member.voice.channel and member.voice.channel.id in channels_voice:
                self.add_points(member, guild)


        if guild_id in self.voice_timers and user_id in self.voice_timers[guild_id]:
            del self.voice_timers[guild_id][user_id]

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        guild_id = member.guild.id
        user_id = member.id

        if after.channel and after.channel.id in channels_voice:
            if guild_id not in self.voice_timers:
                self.voice_timers[guild_id] = {}

            if user_id not in self.voice_timers[guild_id]:
                self.voice_timers[guild_id][user_id] = asyncio.create_task(self.track_voice_time(member, member.guild))

        elif before.channel and before.channel.id in channels_voice:
            if guild_id in self.voice_timers and user_id in self.voice_timers[guild_id]:
                self.voice_timers[guild_id][user_id].cancel()
                del self.voice_timers[guild_id][user_id]

    def add_points(self, member: disnake.Member, guild: disnake.Guild):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance, voice_hours FROM balances WHERE user_id = ? AND guild_id = ?",
            (str(member.id), str(guild.id))
        )
        result = cursor.fetchone()
        if result:
            cursor.execute(
                "UPDATE balances SET balance = balance + 1, voice_hours = voice_hours + 1 WHERE user_id = ? AND guild_id = ?",
                (str(member.id), str(guild.id))
            )
        else:
            cursor.execute(
                "INSERT INTO balances (user_id, guild_id, balance, voice_hours) VALUES (?, ?, ?, ?)",
                (str(member.id), str(guild.id), 1, 1)
            )
        conn.commit()
        conn.close()


def setup(bot):
    bot.add_cog(VoicePointsCog(bot))
