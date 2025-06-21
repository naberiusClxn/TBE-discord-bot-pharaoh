import disnake
from disnake.ext import commands
from datetime import datetime
from config import request_channel_id, commands_id
from main import author_icon_path_notif


class WorktCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(description="Запросить токен")
    async def workt(self, inter: disnake.ApplicationCommandInteraction, attachment: disnake.Attachment = None):
        if not any(role.id in commands_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        file = disnake.File(author_icon_path_notif, filename="Notification.png")
        embed = disnake.Embed(description="Запрос на токен")
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

            if attachment:
                request_embed.set_image(url=attachment.url)
                await request_channel.send(embed=request_embed)
            else:
                await request_channel.send(embed=request_embed)


def setup(bot):
    bot.add_cog(WorktCog(bot))
