import disnake
import sqlite3
import asyncio
from disnake.ext import commands
from datetime import datetime, timedelta
from config import moderation_role_id

class RollvVoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.create_tables()
        self.active_sessions = {}
        self.roll_start_time = None
        self.restore_active_rolls()
        self.update_task = self.bot.loop.create_task(self.update_voice_time())

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS voice_time (
                            user_id INTEGER PRIMARY KEY,
                            time_spent INTEGER DEFAULT 0)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS rollv (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            gift TEXT,
                            end_time TIMESTAMP)''')
        conn.commit()
        conn.close()

    def restore_active_rolls(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, gift, strftime('%Y-%m-%d %H:%M:%S', end_time) FROM rollv WHERE end_time > ?",
                       (datetime.utcnow().isoformat(),))
        active_rolls = cursor.fetchall()
        conn.close()

        for roll_id, gift, end_time_str in active_rolls:
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            time_remaining = (end_time - datetime.utcnow()).total_seconds()
            if time_remaining > 0:
                asyncio.create_task(self.end_rollv(roll_id, gift, time_remaining))

    async def update_voice_time(self):
        while True:
            await asyncio.sleep(1)
            now = datetime.utcnow()
            for user_id, start_time in list(self.active_sessions.items()):
                delta = (now - start_time).total_seconds()
                self.update_time(user_id, delta)
                self.active_sessions[user_id] = now

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if self.roll_start_time and hasattr(self, "active_channels") and self.active_channels:
            now = datetime.utcnow()

            if after.channel and after.channel.id in self.active_channels:
                if member.id not in self.active_sessions:
                    self.active_sessions[member.id] = now

            if before.channel and member.id in self.active_sessions:
                start_time = self.active_sessions.pop(member.id, None)
                if start_time:
                    time_spent = (now - start_time).total_seconds()
                    self.update_time(member.id, time_spent)

    def update_time(self, user_id, time_spent):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO voice_time (user_id, time_spent)
                          VALUES (?, ?) ON CONFLICT(user_id)
                          DO UPDATE SET time_spent = time_spent + ?''',
                       (user_id, time_spent, time_spent))
        conn.commit()
        conn.close()

    @commands.slash_command(description="Раздача среди топов войса")
    async def rollv(self, inter: disnake.ApplicationCommandInteraction, duration: int, gift: str, channels: str):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        self.roll_start_time = datetime.utcnow()
        end_time = self.roll_start_time + timedelta(minutes=duration)

        channel_ids = set(map(int, channels.replace(" ", "").split(",")))
        self.active_channels = channel_ids

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO rollv (gift, end_time) VALUES (?, ?)", (gift, end_time))
        roll_id = cursor.lastrowid
        conn.commit()
        conn.close()

        mention_channels = " ".join(f"<#{channel_id}>" for channel_id in channel_ids)

        embed = disnake.Embed(title="🎉 Голосовая раздача!", color=disnake.Color.green())
        embed.description = (
            f"**Создал:** {inter.author.mention}\n"
            f"**Награда:** {gift}\n"
            f"**ID:** {roll_id}\n"
            f"**Окончание:** {end_time.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            f"**Комнаты:** {mention_channels}"
        )
        await inter.channel.send(embed=embed)

        for channel_id in channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel:
                for member in channel.members:
                    if member.id not in self.active_sessions:
                        self.active_sessions[member.id] = datetime.utcnow()
                    self.update_time(member.id, 0)

        asyncio.create_task(
            self.end_rollv(roll_id, gift, (end_time - datetime.utcnow()).total_seconds(), inter.channel))

    async def end_rollv(self, roll_id, gift, delay, channel):
        await asyncio.sleep(delay)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, SUM(time_spent) AS total_time
            FROM voice_time
            GROUP BY user_id
            ORDER BY total_time DESC
            LIMIT 3
        """)
        top_users = cursor.fetchall()

        cursor.execute("DELETE FROM rollv WHERE id = ?", (roll_id,))
        conn.commit()
        conn.close()

        embed = disnake.Embed(title="🎉 Розыгрыш завершен!", color=disnake.Color.red())

        if top_users:
            winners = "\n".join([f"<@{user[0]}> — {int(user[1])} секунд" for user in top_users])
            embed.description = f"**Приз:** {gift}\n\n**Топ-участники:**\n{winners}"
        else:
            embed.description = "Розыгрыш завершен, но никто не участвовал."

        await channel.send(embed=embed)

        self.roll_start_time = None
        self.active_sessions.clear()
        self.active_channels.clear()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM voice_time")
        conn.commit()
        conn.close()


def setup(bot):
    bot.add_cog(RollvVoiceCog(bot))
