import disnake
import sqlite3
import random
import asyncio
from disnake.ext import commands
from datetime import datetime, timedelta
from config import moderation_role_id

class RollaVoiceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.create_table()
        self.bot.loop.create_task(self.restore_voice_rolls())

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_rolls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    creator_id INTEGER,
                    gift TEXT,
                    end_time TEXT,
                    winner_id INTEGER
                )
            """)
            conn.commit()

    async def restore_voice_rolls(self):
        await self.bot.wait_until_ready()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, end_time, gift FROM voice_rolls WHERE winner_id IS NULL")
            active_rolls = cursor.fetchall()

        for roll_id, end_time_str, gift in active_rolls:
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            remaining_time = max(0, (end_time - datetime.utcnow()).total_seconds())

            async for message in self.bot.get_all_channels():
                if isinstance(message, disnake.TextChannel):
                    async for msg in message.history(limit=100):
                        if msg.embeds and f"**ID:** {roll_id}" in msg.embeds[0].description:
                            self.bot.loop.create_task(self.end_rolla(roll_id, msg, [], gift))
                            break

    @commands.slash_command(description="Раздача среди пользователей в голосовых каналах")
    async def rolla(self, inter: disnake.ApplicationCommandInteraction, duration: int, gift: str, channels: str):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(minutes=duration)
        formatted_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        channel_ids = [int(cid) for cid in channels.split(',')]
        channel_mentions = []

        for channel_id in channel_ids:
            channel = inter.guild.get_channel(channel_id)
            if channel and isinstance(channel, disnake.VoiceChannel):
                channel_mentions.append(channel.mention)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO voice_rolls (creator_id, gift, end_time) VALUES (?, ?, ?)",
                           (inter.author.id, gift, formatted_time))
            roll_id = cursor.lastrowid
            conn.commit()

        embed = disnake.Embed(title="🎉 Голосовая раздача!", color=disnake.Color.green())
        embed.description = (
            f"**Создал:** {inter.author.mention}\n"
            f"**Награда:** {gift}\n"
            f"**ID:** {roll_id}\n"
            f"**Окончание:** {formatted_time} UTC\n"
            f"**Комнаты:** {', '.join(channel_mentions) if channel_mentions else '❌ Комнаты не найдены'}"
        )

        message = await inter.channel.send(embed=embed)
        self.bot.loop.create_task(self.end_rolla(roll_id, message, channel_ids, gift))

    async def end_rolla(self, roll_id, message, channel_ids, gift):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT end_time FROM voice_rolls WHERE id = ?", (roll_id,))
            roll = cursor.fetchone()
            if not roll:
                return

        end_time = datetime.strptime(roll[0], "%Y-%m-%d %H:%M:%S")
        await asyncio.sleep(max(0, (end_time - datetime.utcnow()).total_seconds()))
        await self.pick_winner(roll_id, message, channel_ids, gift)

    async def pick_winner(self, roll_id, message, channel_ids, gift):
        guild = message.guild
        participants = []

        for channel_id in channel_ids:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, disnake.VoiceChannel):
                participants.extend(member.id for member in channel.members)

        winner_id = random.choice(participants) if participants else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE voice_rolls SET winner_id = ? WHERE id = ?", (winner_id, roll_id))
            conn.commit()

        embed = message.embeds[0]
        embed.color = disnake.Color.red()

        if winner_id:
            winner = await self.bot.fetch_user(winner_id)
            embed.description += f"\n\n🎉 **Победитель:** {winner.mention}!"
        else:
            embed.description += "\n\n❌ **Победитель не определён.** Никто не участвовал."

        await message.edit(embed=embed)

    @commands.slash_command(description="Досрочно завершить розыгрыш")
    async def endrolla(self, inter: disnake.ApplicationCommandInteraction, roll_id: int):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT gift FROM voice_rolls WHERE id = ?", (roll_id,))
            roll = cursor.fetchone()
            if not roll:
                await inter.response.send_message("Розыгрыш с таким ID не найден.", ephemeral=True)
                return

        await inter.response.send_message(f"Розыгрыш ID {roll_id} завершается...", ephemeral=True)
        async for message in inter.channel.history(limit=100):
            if message.embeds and f"**ID:** {roll_id}" in message.embeds[0].description:
                await self.pick_winner(roll_id, message, [], roll[0])
                break


def setup(bot):
    bot.add_cog(RollaVoiceCog(bot))
