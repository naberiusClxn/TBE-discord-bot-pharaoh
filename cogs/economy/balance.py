import disnake
from disnake.ext import commands
import sqlite3

class BalanceCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    @commands.slash_command(description="Посмотреть баланс пользователя")
    async def balance(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        user = user or inter.author
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE user_id = ? AND guild_id = ?",
                       (str(user.id), str(inter.guild.id)))
        result = cursor.fetchone()
        conn.close()

        balance = result[0] if result else 0

        embed = disnake.Embed(
            title=f"Баланс пользователя {user.display_name}",
            description=f"Баланс: {balance}",
            color=disnake.Color.blue()
        )
        await inter.response.send_message(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(BalanceCog(bot))
