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
                    winner_id INTEGER,
                    channel_ids TEXT
                )
            """)

            cursor.execute("PRAGMA table_info(voice_rolls)")
            columns = [column[1] for column in cursor.fetchall()]
            if "channel_ids" not in columns:
                cursor.execute("ALTER TABLE voice_rolls ADD COLUMN channel_ids TEXT")

            conn.commit()

    async def restore_voice_rolls(self):
        await self.bot.wait_until_ready()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, end_time, gift, channel_ids FROM voice_rolls WHERE winner_id IS NULL")
            active_rolls = cursor.fetchall()

        for roll_id, end_time_str, gift, channel_ids_str in active_rolls:
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
            channel_ids = [int(cid) for cid in channel_ids_str.split(",")] if channel_ids_str else []


            found = False
            for guild in self.bot.guilds:
                for channel in guild.text_channels:
                    try:
                        async for message in channel.history(limit=100):
                            if message.embeds and message.embeds[0].description and f"**ID:** {roll_id}" in \
                                    message.embeds[0].description:
                                self.bot.loop.create_task(self.end_rolla(roll_id, message, channel_ids, gift, end_time))
                                found = True
                                break
                        if found:
                            break
                    except disnake.Forbidden:
                        continue
                if found:
                    break

            if not found:
                print(f"Сообщение с розыгрышем ID {roll_id} не найдено.")

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
            cursor.execute("INSERT INTO voice_rolls (creator_id, gift, end_time, channel_ids) VALUES (?, ?, ?, ?)",
                           (inter.author.id, gift, formatted_time, ",".join(map(str, channel_ids))))
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
        self.bot.loop.create_task(self.end_rolla(roll_id, message, channel_ids, gift, end_time))

    async def end_rolla(self, roll_id, message, channel_ids, gift, end_time):
        remaining_time = max(0, (end_time - datetime.utcnow()).total_seconds())

        if remaining_time > 0:
            print(f"Розыгрыш ID {roll_id} завершится через {remaining_time} секунд.")
            await asyncio.sleep(remaining_time)

        await self.pick_winner(roll_id, message, channel_ids, gift)

    async def pick_winner(self, roll_id, message, channel_ids, gift):
        guild = message.guild
        participants = []

        for channel_id in channel_ids:
            channel = guild.get_channel(channel_id)
            if channel and isinstance(channel, disnake.VoiceChannel):
                participants.extend(member.id for member in channel.members)

        if participants:
            winner_id = random.choice(participants)
        else:
            winner_id = None

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
            cursor.execute("SELECT gift, channel_ids FROM voice_rolls WHERE id = ?", (roll_id,))
            roll = cursor.fetchone()
            if not roll:
                await inter.response.send_message("Розыгрыш с таким ID не найден.", ephemeral=True)
                return

        gift, channel_ids_str = roll
        channel_ids = [int(cid) for cid in channel_ids_str.split(",")] if channel_ids_str else []

        await inter.response.send_message(f"Розыгрыш ID {roll_id} завершается...", ephemeral=True)
        async for message in inter.channel.history(limit=100):
            if message.embeds and f"**ID:** {roll_id}" in message.embeds[0].description:
                await self.pick_winner(roll_id, message, channel_ids, gift)
                break
        else:
            await inter.followup.send("Сообщение с розыгрышем не найдено.", ephemeral=True)




def setup(bot):
    bot.add_cog(RollaVoiceCog(bot))