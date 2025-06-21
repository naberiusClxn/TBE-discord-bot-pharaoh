import disnake
from disnake.ext import commands
import sqlite3
from config import moderation_role_id
from main import author_icon_path_notif


class TaketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    @commands.slash_command(description="Забрать токен у участника")
    async def taket(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, tokens: int):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        if tokens <= 0:
            await inter.response.send_message("Количество токенов должно быть больше нуля.", ephemeral=True)
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for _ in range(tokens):
            cursor.execute("""
                DELETE FROM punishments 
                WHERE user_id = ? AND guild_id = ? AND type = 'TOKEN' 
                ORDER BY created_at DESC LIMIT 1
            """, (str(user.id), str(inter.guild.id)))

        conn.commit()
        conn.close()

        file = disnake.File(author_icon_path_notif, filename="Notification.png")
        embed = disnake.Embed(
            description=f"{tokens} токенов у пользователя {user.mention} были отняты!")
        embed.set_author(name="Экономика", icon_url=f"attachment://Notification.png")
        await inter.response.send_message(embed=embed, ephemeral=True, file=file)

def setup(bot):
    bot.add_cog(TaketCog(bot))
