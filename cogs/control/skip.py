import disnake
from disnake.ext import commands
from config import moderation_role_id, skip_role_id

class SkipCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Выдать доступ к приватным комнатам")
    async def skip(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        role = inter.guild.get_role(skip_role_id)
        if not role:
            return
        await user.add_roles(role)

def setup(bot):
    bot.add_cog(SkipCog(bot))
