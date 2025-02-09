import disnake
from disnake.ext import commands
import sqlite3
from other.db_utils import create_tables
from config import moderation_role_id
from main import author_icon_path

class UnwarnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        create_tables(self.db_path)

    @commands.slash_command(name="unwarn", description="Снимает предупреждение")
    async def unwarn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM punishments WHERE user_id = ? AND guild_id = ? AND type = ?", (str(member.id), str(inter.guild.id), "warn"))
            conn.commit()
            conn.close()
            file = disnake.File(author_icon_path, filename="hammer.png")
            embed = disnake.Embed(
                description=f"Пользователю {member.mention} были сняты предупреждения")
            embed.set_author(name="Снятие наказания", icon_url=f"attachment://hammer.png")
            await inter.response.send_message(embed=embed, ephemeral=True, file=file)
        except Exception as e:
            await inter.response.send_message(f"{e}", ephemeral=True)

def setup(bot):
    bot.add_cog(UnwarnCog(bot))
