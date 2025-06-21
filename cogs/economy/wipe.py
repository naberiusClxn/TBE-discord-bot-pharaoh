import disnake
from disnake.ext import commands
import sqlite3

from config import admin_status


class WipeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.percent_roles = {
            "1%": 1339649732343238697,
            "2%": 1339649904217161738,
            "3%": 1339650095695663174
        }

    @commands.slash_command(description="Полный вайп балансов")
    async def wipe(self, inter: disnake.ApplicationCommandInteraction):
        if not any(role.id == admin_status for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        class ConfirmView(disnake.ui.View):
            def __init__(self, db_path, percent_roles):
                super().__init__(timeout=30)
                self.db_path = db_path
                self.percent_roles = percent_roles

            @disnake.ui.button(label="Подтвердить", style=disnake.ButtonStyle.danger)
            async def confirm(self, button: disnake.ui.Button, interaction: disnake.MessageInteraction):
                if interaction.author != inter.author:
                    await interaction.response.send_message("Вы не можете подтвердить этот запрос.", ephemeral=True)
                    return

                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                try:
                    cursor.execute("UPDATE balances SET balance = 0")
                    cursor.execute("DELETE FROM purchases")
                    conn.commit()

                    for member in inter.guild.members:
                        for role_name, role_id in self.percent_roles.items():
                            role = inter.guild.get_role(role_id)
                            if role and role in member.roles:
                                await member.remove_roles(role)

                    await inter.edit_original_message(content="Все балансы, предметы и роли были успешно удалены!",
                                                      view=None)
                except Exception as e:
                    conn.rollback()
                    await inter.edit_original_message(content=f"Ошибка: {e}", view=None)
                finally:
                    conn.close()

        view = ConfirmView(self.db_path, self.percent_roles)
        await inter.response.send_message("Вы уверены, что хотите удалить все балансы, предметы и роли?", view=view,
                                          ephemeral=True)


def setup(bot):
    bot.add_cog(WipeCog(bot))
