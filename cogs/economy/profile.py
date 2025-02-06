import disnake
from disnake.ext import commands
import sqlite3

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    @commands.slash_command(description="Посмотреть профиль пользователя")
    async def profile(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        user = user or inter.author

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM punishments 
            WHERE user_id = ? AND guild_id = ? AND type = 'TOKEN'
        """, (str(user.id), str(inter.guild.id)))

        token_count = cursor.fetchone()[0]
        conn.close()

        embed = disnake.Embed(title=f"Профиль {user.display_name}", color=disnake.Color.blue())
        embed.set_thumbnail(url=user.avatar.url if user.avatar else None)
        embed.add_field(name="Токены опыта", value=str(token_count), inline=False)

        await inter.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(ProfileCog(bot))
