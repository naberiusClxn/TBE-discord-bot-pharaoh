import disnake
from disnake.ext import commands
import sqlite3


class StorageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    def get_purchases(self, user_id: str, guild_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT item_name, cost, purchase_date FROM purchases
            WHERE user_id = ? AND guild_id = ?
            ORDER BY purchase_date DESC
        """, (user_id, guild_id))
        purchases = cursor.fetchall()
        conn.close()
        return purchases

    @commands.slash_command(description="Показать купленные товары")
    async def storage(self, inter: disnake.ApplicationCommandInteraction):
        user_id = str(inter.user.id)
        guild_id = str(inter.guild.id)

        purchases = self.get_purchases(user_id, guild_id)

        if not purchases:
            await inter.response.send_message("У вас пока нет купленных товаров.", ephemeral=True)
            return

        embeds = []
        for item_name, cost, purchase_date in purchases:
            embed = disnake.Embed(
                title=f"Товар: {item_name}",
                description=f"Стоимость: {cost} монет\nДата покупки: {purchase_date}",
                color=disnake.Color.blue()
            )
            embeds.append(embed)

        await inter.response.send_message(embeds=embeds, ephemeral=True)


def setup(bot):
    bot.add_cog(StorageCog(bot))
