import disnake
import sqlite3
import random
import asyncio
from disnake.ext import commands
from datetime import datetime, timedelta
from config import moderation_role_id

class RollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.create_table()
        self.bot.loop.create_task(self.restore_rolls())

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rolls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    channel_id INTEGER,
                    creator_id INTEGER,
                    gift TEXT,
                    end_time TEXT,
                    winner_id INTEGER
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS participants (
                    roll_id INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY (roll_id) REFERENCES rolls (id)
                )
            """)
            conn.commit()

    @commands.slash_command(description="Создать розыгрыш")
    async def roll(self, inter: disnake.ApplicationCommandInteraction, duration: int, gift: str = "Награда"):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        end_time = datetime.utcnow() + timedelta(minutes=duration)
        formatted_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO rolls (channel_id, creator_id, gift, end_time) VALUES (?, ?, ?, ?)",
                           (inter.channel.id, inter.author.id, gift, formatted_time))
            roll_id = cursor.lastrowid
            conn.commit()

        embed = disnake.Embed(title="🎉 Розыгрыш!", color=disnake.Color.green())
        embed.description = (
            f"**Создал:** {inter.author.mention}\n"
            f"**Награда:** {gift}\n"
            f"**ID:** {roll_id}\n"
            f"**Участники:** 0\n"
            f"**Окончание:** {formatted_time} UTC"
        )

        view = RollView(roll_id, self.db_path)
        message = await inter.channel.send(embed=embed, view=view)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE rolls SET message_id = ? WHERE id = ?", (message.id, roll_id))
            conn.commit()

        self.bot.add_view(view)

        self.bot.loop.create_task(self.end_roll(roll_id, message.id, inter.channel.id, formatted_time, gift))

    async def restore_rolls(self):
        await self.bot.wait_until_ready()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, message_id, channel_id, end_time, gift FROM rolls WHERE winner_id IS NULL")
            active_rolls = cursor.fetchall()

        for roll_id, message_id, channel_id, end_time, gift in active_rolls:
            self.bot.add_view(RollView(roll_id, self.db_path))
            self.bot.loop.create_task(self.end_roll(roll_id, message_id, channel_id, end_time, gift))

    async def end_roll(self, roll_id, message_id, channel_id, end_time_str, gift):
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        await asyncio.sleep(max(0, (end_time - datetime.utcnow()).total_seconds()))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT winner_id FROM rolls WHERE id = ?", (roll_id,))
            existing_winner = cursor.fetchone()

            if existing_winner and existing_winner[0] is not None:
                return

            cursor.execute("SELECT user_id FROM participants WHERE roll_id = ?", (roll_id,))
            participants = cursor.fetchall()

            cursor.execute("SELECT message_id FROM rolls WHERE id = ?", (roll_id,))
            roll = cursor.fetchone()
            if not roll:
                return

            winner_id = None
            if participants:
                winner_id = random.choice(participants)[0]
                cursor.execute("UPDATE rolls SET winner_id = ? WHERE id = ?", (winner_id, roll_id))
                conn.commit()

        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        try:
            message = await channel.fetch_message(message_id)
        except disnake.NotFound:
            return

        embed = message.embeds[0]
        embed.color = disnake.Color.red()

        if winner_id:
            winner = await self.bot.fetch_user(winner_id)
            embed.description += f"\n\n🎉 **Победитель:** {winner.mention}!"
        else:
            embed.description += "\n\n❌ **Победитель не определён.** Никто не участвовал."

        await message.edit(embed=embed, view=None)


class RollView(disnake.ui.View):
    def __init__(self, roll_id: int, db_path: str):
        super().__init__(timeout=None)
        self.roll_id = roll_id
        self.db_path = db_path

    @disnake.ui.button(label="Участвовать", style=disnake.ButtonStyle.green, custom_id="join_roll")
    async def join_button(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT end_time FROM rolls WHERE id = ?", (self.roll_id,))
            roll = cursor.fetchone()

            if not roll:
                await inter.response.send_message("Этот розыгрыш уже завершён.", ephemeral=True)
                return

            end_time = datetime.strptime(roll[0], "%Y-%m-%d %H:%M:%S")

            if datetime.utcnow() >= end_time:
                await inter.response.send_message("Розыгрыш уже завершён!", ephemeral=True)
                return

            cursor.execute("SELECT user_id FROM participants WHERE roll_id = ? AND user_id = ?", (self.roll_id, inter.author.id))
            if cursor.fetchone():
                await inter.response.send_message("Вы уже участвуете в этом розыгрыше!", ephemeral=True)
                return

            cursor.execute("INSERT INTO participants (roll_id, user_id) VALUES (?, ?)", (self.roll_id, inter.author.id))
            conn.commit()

            cursor.execute("SELECT COUNT(*) FROM participants WHERE roll_id = ?", (self.roll_id,))
            participant_count = cursor.fetchone()[0]

        try:
            message = await inter.channel.fetch_message(inter.message.id)
            embed = message.embeds[0]
            embed.description = embed.description.replace(
                f"**Участники:** {participant_count - 1}", f"**Участники:** {participant_count}"
            )
            await message.edit(embed=embed)
        except Exception as e:
            print(f"{e}")

        await inter.response.send_message("Вы успешно участвуете!", ephemeral=True)

def setup(bot):
    bot.add_cog(RollCog(bot))
