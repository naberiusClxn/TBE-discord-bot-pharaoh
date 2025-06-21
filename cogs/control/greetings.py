import disnake
from disnake.ext import commands
from config import greetings_channel_id

class GreetingsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: disnake.Member):
        channel = member.guild.get_channel(greetings_channel_id)
        if channel:
            embed = disnake.Embed(
                description=f"## Приветствую <@{member.id}>\n> **Добро пожаловать в нашу команду -** TBE TEAM",
                color=disnake.Color.red()
            )
            embed.set_thumbnail(url="https://i.imgur.com/TDi3EP4.gif")
            await channel.send(embed=embed)

def setup(bot):
    bot.add_cog(GreetingsCog(bot))
