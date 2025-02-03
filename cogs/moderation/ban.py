import disnake
from disnake.ext import commands
import sqlite3
from datetime import datetime, timedelta
from config import moderation_role_id
from main import author_icon_path

class BanCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    @commands.slash_command(description="Забанить пользователя")
    async def ban(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member, duration: int = None,
                  reason: str = "Не указана"):
        expires_at = int((datetime.utcnow() + timedelta(minutes=duration)).timestamp()) if duration else None
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        try:
            await inter.guild.ban(user, reason=reason)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO punishments (user_id, guild_id, type, reason, expires_at) 
                VALUES (?, ?, ?, ?, ?)""",
                           (user.id, inter.guild.id, "ban", reason, expires_at)
                           )
            conn.commit()
            conn.close()
            file = disnake.File(author_icon_path, filename="hammer.png")
            if duration:
                embed = disnake.Embed(
                    description=f"Пользователь {user.mention} забанен на {duration} минут. Причина: {reason}")
                embed.set_author(name="Выдача наказания", icon_url=f"attachment://hammer.png")
                await inter.response.send_message(embed=embed, ephemeral=True, file=file)
            else:
                embed = disnake.Embed(
                    description=f"Пользователь {user.mention} забанен навсегда. Причина: {reason}")
                embed.set_author(name="Выдача наказания", icon_url=f"attachment://hammer.png")
                await inter.response.send_message(embed=embed, ephemeral=True, file=file)
        except Exception as e:
            await inter.response.send_message(f"{e}", ephemeral=True)


def setup(bot):
    bot.add_cog(BanCog(bot))
