import disnake
from disnake.ext import commands
import sqlite3
from datetime import datetime
from config import moderation_role_id
from main import author_icon_path_notif

class GivetCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    @commands.slash_command(description="Выдать токен участнику")
    async def givet(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO punishments (user_id, guild_id, type, reason, created_at) 
            VALUES (?, ?, 'TOKEN', 'Выдан токен', ?)
        """, (str(user.id), str(inter.guild.id), int(datetime.utcnow().timestamp())))

        conn.commit()
        conn.close()

        file = disnake.File(author_icon_path_notif, filename="Notification.png")
        embed = disnake.Embed(
            description=f"Токен успешно выдан пользователю {user.mention}!")
        embed.set_author(name="Экономика", icon_url=f"attachment://Notification.png")
        await inter.response.send_message(embed=embed, ephemeral=True, file=file)

def setup(bot):
    bot.add_cog(GivetCog(bot))
