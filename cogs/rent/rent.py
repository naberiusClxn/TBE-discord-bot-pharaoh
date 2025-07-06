import disnake
from disnake import ApplicationCommandInteraction
from disnake.ext import commands

from rent.buttons.RentButtonView import RentButtonView
from config import moderation_role_id


class RentCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="rent", description="Создать сообщение с арендой")
    async def rent(self, inter: ApplicationCommandInteraction):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)

        embed = disnake.Embed(
            description=(
                "## Аренда\n"
                "В этом разделе ты можешь арендовать CS-аккаунт."
                "Все аккаунты верифицированы в Китае, настроены и полностью готовы к работе."
                "\n\nУсловия аренды:\n\n"
                "1) Мы удерживаем 10% от каждого лога в качестве платы за аренду.\n"
                "2) Аренда аккаунта подразумевает ежедневную активность — 8+ игр в день (исключения оговариваются индивидуально/заранее).\n"
                "3) Аренда подразумевает ежедневную отчётность по завершённым играм/логам (скриншотами).\n\n"
                "Если согласен с условиями, жми на кнопку ниже."
            ),
            color=disnake.Color.red()
        )

        await inter.channel.send(embed=embed, view=RentButtonView())
def setup(bot):
    bot.add_cog(RentCog(bot))
