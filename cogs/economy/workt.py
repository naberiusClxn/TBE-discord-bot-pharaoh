import disnake
from disnake.ext import commands
from datetime import datetime
from config import request_channel_id
from main import author_icon_path_notif

class WorktCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Запросить токен")
    async def workt(self, inter: disnake.ApplicationCommandInteraction):
        file = disnake.File(author_icon_path_notif, filename="Notification.png")
        embed = disnake.Embed(
            description=f"Запрос на токен"
        )
        embed.set_author(name="Уведомление", icon_url=f"attachment://Notification.png")
        await inter.response.send_message(embed=embed, ephemeral=True, file=file)

        request_channel = self.bot.get_channel(request_channel_id)
        if request_channel:
            request_embed = disnake.Embed(
                description=f"Участник {inter.author.mention} \n({inter.author})\nзапросил токен.",
            )
            request_embed.set_author(name="Запрос на токен", icon_url=f"attachment://Notification.png")
            request_embed.set_thumbnail(url=inter.author.avatar.url)
            request_embed.timestamp = datetime.now()
            await request_channel.send(embed=request_embed)

def setup(bot):
    bot.add_cog(WorktCog(bot))
