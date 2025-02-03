import disnake
from disnake.ext import commands
import sqlite3
from db_utils import create_tables
from config import moderation_role_id

class UnmuteCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.author_icon_url = "https://cdn.discordapp.com/attachments/1312804207186804810/1334651866276954162/Ban_Hammer.png?ex=67a1ec29&is=67a09aa9&hm=306ff3a184b0814ce8cfd7a932bda2ce1754988c3e3e4f73a4a61cb5ff591238&"
        create_tables(self.db_path)

    @commands.slash_command(name="unmute", description="Снимает таймаут")
    async def unmute(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, reason: str):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return
        try:
            await member.edit(timeout=None, reason=reason)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM punishments WHERE user_id = ? AND guild_id = ? AND type = ?", (str(member.id), str(inter.guild.id), "mute"))
            conn.commit()
            conn.close()

            embed = disnake.Embed(
                description=f"Пользователю {member.mention} был снят таймаут. Причина: {reason}")
            embed.set_author(name="Снятие наказания", icon_url=self.author_icon_url)
            await inter.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await inter.response.send_message(f"{e}", ephemeral=True)

def setup(bot):
    bot.add_cog(UnmuteCog(bot))

