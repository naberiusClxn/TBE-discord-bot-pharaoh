from datetime import datetime
import disnake
import sqlite3
import random
from disnake.ext import commands
from config import moderation_role_id


class RollsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    @commands.slash_command(description="Немедленно назначить победителя раздачи")
    async def rolls(self, inter: disnake.ApplicationCommandInteraction, roll_id: int):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT message_id, channel_id, winner_id, gift FROM rolls WHERE id = ?", (roll_id,))
            roll = cursor.fetchone()

            if not roll:
                await inter.response.send_message("Розыгрыш с таким ID не найден.", ephemeral=True)
                return

            message_id, channel_id, winner_id, gift = roll

            if winner_id is not None:
                await inter.response.send_message("Этот розыгрыш уже завершён.", ephemeral=True)
                return

            cursor.execute("SELECT user_id FROM participants WHERE roll_id = ?", (roll_id,))
            participants = cursor.fetchall()

            if not participants:
                await inter.response.send_message("В этом розыгрыше нет участников!", ephemeral=True)
                return

            winner_id = random.choice(participants)[0]
            cursor.execute("UPDATE rolls SET winner_id = ?, end_time = ? WHERE id = ?",
                           (winner_id, datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), roll_id))
            conn.commit()

        channel = inter.guild.get_channel(channel_id)
        if not channel:
            await inter.response.send_message("Канал с розыгрышем не найден.", ephemeral=True)
            return

        try:
            message = await channel.fetch_message(message_id)
        except disnake.NotFound:
            await inter.response.send_message("Сообщение розыгрыша не найдено.", ephemeral=True)
            return

        winner = await self.bot.fetch_user(winner_id)

        embed = message.embeds[0]
        embed.color = disnake.Color.red()
        embed.description += f"\n\n🎉 **Победитель:** {winner.mention}!"

        await message.edit(embed=embed, view=None)
        await inter.response.send_message(f"Розыгрыш {roll_id} завершён! Победитель: {winner.mention}", ephemeral=True)

        self.bot.loop.create_task(self.cancel_scheduled_roll(roll_id))

    async def cancel_scheduled_roll(self, roll_id: int):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT end_time FROM rolls WHERE id = ?", (roll_id,))
            roll = cursor.fetchone()

        if not roll:
            return

        cursor.execute("UPDATE rolls SET end_time = NULL WHERE id = ?", (roll_id,))
        conn.commit()


def setup(bot):
    bot.add_cog(RollsCog(bot))
