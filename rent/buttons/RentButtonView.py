import disnake
from disnake.ext import commands
from disnake.ui import View, Button
from config import category_rent, category_rent_apply, rent_role_id
from rent.database.database_util import remove_rent_channel, add_rent_channel


class RentButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @disnake.ui.button(
        label="Подать заявку",
        style=disnake.ButtonStyle.primary,
        custom_id="open_rent_form"
    )
    async def rent_button_callback(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        guild = inter.guild
        author = inter.author

        for ch in guild.text_channels:
            if (
                ch.name == f"заявка_{author.display_name.lower().replace(' ', '-')}"
                and ch.category_id == category_rent
            ):
                await inter.response.send_message("У вас уже есть открытая заявка.", ephemeral=True)
                return

        category = disnake.utils.get(guild.categories, id=category_rent)
        if not category:
            await inter.response.send_message("Категория для аренды не найдена.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: disnake.PermissionOverwrite(read_messages=False),
            author: disnake.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.get_role(rent_role_id): disnake.PermissionOverwrite(read_messages=True, send_messages=True),
        }

        channel = await guild.create_text_channel(
            name=f"заявка_{author.display_name.lower().replace(' ', '-')}",
            category=category,
            overwrites=overwrites,
            reason="Создана заявка на аренду"
        )
        add_rent_channel(channel.id)

        embed = disnake.Embed(
            title="Новая заявка на аренду",
            description=(
                f"Пользователь {author.mention} оставил заявку.\n\n"
                f"**Для ускоренного рассмотрения заявки, ответь на следующие вопросы:**\n"
                f"1) Согласен ли ты с условиями аренды?\n"
                f"2) На какой срок ты планируешь арендовать аккаунт?\n"
                f"3) Укажите свой Telegram (для связи в резервном случае)."
            ),
            color=disnake.Color.green()
        )

        view = RentModerationView(channel.id)
        await channel.send(embed=embed, view=view)

        await inter.response.send_message(f"Канал {channel.mention} создан.", ephemeral=True)


class RentModerationView(View):
    def __init__(self, channel_id: int):
        super().__init__(timeout=None)
        self.channel_id = channel_id

    @disnake.ui.button(emoji="✅", custom_id="approve_rent")
    async def approve_callback(self, button: Button, inter: disnake.MessageInteraction):
        if rent_role_id not in [role.id for role in inter.author.roles]:
            return await inter.response.send_message("У вас нет прав на это действие.", ephemeral=True)

        channel = inter.guild.get_channel(self.channel_id)
        if not channel:
            return

        category = disnake.utils.get(inter.guild.categories, id=category_rent_apply)
        if not category:
            return await inter.response.send_message("Категория для одобренных заявок не найдена.", ephemeral=True)

        await channel.edit(category=category, reason="Заявка одобрена")

        await inter.message.edit(view=None)
        await inter.response.send_message("Заявка одобрена. Канал перемещен.", ephemeral=True)

    @disnake.ui.button(emoji="❌", custom_id="deny_rent")
    async def deny_callback(self, button: Button, inter: disnake.MessageInteraction):
        if rent_role_id not in [role.id for role in inter.author.roles]:
            return await inter.response.send_message("У вас нет прав на это действие.", ephemeral=True)

        await inter.message.edit(view=None)
        await inter.response.send_message("Заявка отклонена. Канал будет удален.", ephemeral=True)

        channel = inter.guild.get_channel(self.channel_id)
        if channel:
            await channel.delete(reason="Заявка отклонена")
            remove_rent_channel(channel.id)