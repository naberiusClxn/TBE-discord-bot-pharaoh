import disnake
from disnake.ext import commands
import sqlite3

from config import moderation_role_id


class AgiveCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    async def update_balance(self, user_id, guild_id, amount):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        result = cursor.fetchone()

        if result:
            new_balance = result[0] + amount
            cursor.execute("UPDATE balances SET balance = ? WHERE user_id = ? AND guild_id = ?", (new_balance, user_id, guild_id))
        else:
            cursor.execute("INSERT INTO balances (user_id, guild_id, balance) VALUES (?, ?, ?)", (user_id, guild_id, amount))

        conn.commit()
        conn.close()

    @commands.slash_command(description="Назначить серверную валюту пользователю")
    async def agive(self, inter: disnake.ApplicationCommandInteraction, user_id: str, amount: int):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        if amount < 0:
            await inter.response.send_message("Сумма не может быть отрицательной!", ephemeral=True)
            return

        await self.update_balance(user_id, str(inter.guild.id), amount)

        embed = disnake.Embed(
            title="Баланс обновлен",
            description=f"Пользователю <@{user_id}> назначено {amount} серверной валюты.",
            color=disnake.Color.green()
        )
        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(AgiveCog(bot))