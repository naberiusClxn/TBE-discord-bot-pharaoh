import disnake
from disnake.ext import commands
import sqlite3
from config import commands_id


class StorageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.percent_roles = {
            "1%": 1339649732343238697,
            "2%": 1339649904217161738,
            "3%": 1339650095695663174
        }

    def get_purchases(self, user_id: str, guild_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, item_name, cost, purchase_date FROM purchases
            WHERE user_id = ? AND guild_id = ?
            ORDER BY purchase_date DESC
        """, (user_id, guild_id))
        purchases = cursor.fetchall()
        conn.close()
        return purchases

    def remove_purchase(self, purchase_id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM purchases WHERE id = ?", (purchase_id,))
        conn.commit()
        conn.close()

    @commands.slash_command(description="Показать купленные товары")
    async def storage(self, inter: disnake.ApplicationCommandInteraction):
        if not any(role.id in commands_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        user_id = str(inter.user.id)
        guild_id = str(inter.guild.id)
        purchases = self.get_purchases(user_id, guild_id)

        if not purchases:
            await inter.response.send_message("У вас пока нет купленных товаров.", ephemeral=True)
            return

        embeds = []
        view = disnake.ui.View()

        for purchase_id, item_name, cost, purchase_date in purchases:
            embed = disnake.Embed(
                title=f"Товар: {item_name}",
                description=f"Стоимость: {cost} монет\nДата покупки: {purchase_date}",
                color=disnake.Color.blue()
            )
            embeds.append(embed)

            if item_name in self.percent_roles:
                button = disnake.ui.Button(label=f"Применить {item_name}", style=disnake.ButtonStyle.green,
                                           custom_id=str(purchase_id))
                view.add_item(button)

        async def button_callback(interaction: disnake.MessageInteraction):
            purchase_id = int(interaction.data["custom_id"])
            role_id = self.percent_roles.get(next((name for pid, name, _, _ in purchases if pid == purchase_id), None))

            if role_id and interaction.guild:
                role = interaction.guild.get_role(role_id)
                await interaction.user.add_roles(role)
                self.remove_purchase(purchase_id)
                await interaction.response.send_message(f"Вы применили {role.name}!", ephemeral=True)


        for button in view.children:
            button.callback = button_callback

        await inter.response.send_message(embeds=embeds, view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(StorageCog(bot))
