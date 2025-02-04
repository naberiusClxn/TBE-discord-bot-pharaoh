import disnake
from disnake.ext import commands
import sqlite3
from other.db_utils import create_tables
from config import moderation_role_id
from main import author_icon_path

class UnbanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        create_tables(self.db_path)

    @commands.slash_command(name="unban", description="Снимает бан")
    async def unban(self, inter: disnake.ApplicationCommandInteraction, user_id: str, reason: str):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return
        try:
            uid = int(user_id)
            await inter.guild.unban(disnake.Object(id=uid), reason=reason)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM punishments WHERE user_id = ? AND guild_id = ? AND type = ?", (str(uid), str(inter.guild.id), "ban"))
            conn.commit()
            conn.close()
            file = disnake.File(author_icon_path, filename="hammer.png")
            embed = disnake.Embed(
                description=f"Пользователю {user_id} был снят бан")
            embed.set_author(name="Снятие наказания", icon_url=f"attachment://hammer.png")
            await inter.response.send_message(embed=embed, ephemeral=True, file=file)
        except Exception as e:
            await inter.response.send_message(f"{e}", ephemeral=True)

def setup(bot):
    bot.add_cog(UnbanCog(bot))

