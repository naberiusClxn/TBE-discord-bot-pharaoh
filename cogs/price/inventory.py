import re
import asyncio
import disnake
from disnake.ext import commands
import requests

from other.db_utils import add_link
from other.image_util import create_inventory_image
from other.inventory_util import get_inventory_value, get_cs2_item_count, resolve_vanity_url


ALLOWED_GUILD_ID = 1263064633678368818

class InventoryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steamid_pattern = re.compile(
            r"https?://steamcommunity\.com/(?:profiles/(\d{17})|id/([a-zA-Z0-9_-]+))"
        )

    async def resolve_steam_id(self, match):
        if match.group(1):
            return match.group(1)
        elif match.group(2):
            vanity_url = match.group(2)
            return await resolve_vanity_url(vanity_url)
        return None

    @commands.slash_command(name="inventory", description="Показывает инвентарь CS2 по ссылке на профиль Steam")
    async def inventory(self, inter: disnake.ApplicationCommandInteraction, link: str):
        await inter.response.defer(ephemeral=True)
        guild_info = (
            f"{inter.guild.name} ({inter.guild.id})" if inter.guild else "Личные сообщения"
        )
        print(f"Команда /inventory вызвана пользователем {inter.user} на сервере: {guild_info}")


        if not inter.guild or inter.guild.id != ALLOWED_GUILD_ID:
            await inter.edit_original_message(
                "⚠️ Эта команда доступна только на официальном сервере."
            )
            return
        match = self.steamid_pattern.search(link)
        if not match:
            await inter.edit_original_message("⚠️ Указана недействительная ссылка на профиль Steam")
            return

        try:
            steam_id = await self.resolve_steam_id(match)

            if not steam_id:
                await inter.edit_original_message("⚠️ Не удалось определить SteamID из ссылки")
                return

            add_link(link)

            if not steam_id:
                await inter.edit_original_message("⚠️ Не удалось определить SteamID из ссылки")
                return

            loop = asyncio.get_running_loop()
            inventory_data = await asyncio.wait_for(
                loop.run_in_executor(None, get_inventory_value, steam_id),
                timeout=60.0
            )

            total_value, cs2_items, tradable_items, top_items, *_ = inventory_data
            item_count = await asyncio.to_thread(get_cs2_item_count, steam_id)

            top_items_text = ""
            for item in top_items[:6]:
                name = item["name"]
                price = item["price"]
                top_items_text += f"`💴` {name} — {price}\n"

            embed = disnake.Embed(
                description=(
                    f"**Общая информация:**\n"
                    f"`💵` Общая стоимость: ${total_value:.2f}\n"
                    f"`🎒` Всего предметов: {item_count}\n"
                    f"`🟢` Без Trade-ban: {tradable_items}\n\n"
                    f"**Топ дорогих предметов:**\n"
                    f"{top_items_text}"
                ),
            )
            image_urls = [item["image"] for item in top_items[:6] if item.get("image")]

            image_buffer = create_inventory_image(image_urls)
            file = disnake.File(fp=image_buffer, filename="inventory.png")

            embed.set_image(url="attachment://inventory.png")

            await inter.edit_original_message(embed=embed, file=file)

        except asyncio.TimeoutError:
            await inter.edit_original_message("⌛ Превышено время ожидания при обработке инвентаря")
        except ValueError as e:
            if "inventory is private" in str(e).lower():
                await inter.edit_original_message("🔒 Этот аккаунт приватный. Инвентарь недоступен для просмотра.")
            else:
                await inter.edit_original_message(f"⚠️ {str(e)}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                await inter.edit_original_message("🔒 Этот аккаунт приватный. Инвентарь недоступен для просмотра.")
            else:
                await inter.edit_original_message(f"⚠️ Ошибка при обработке инвентаря: {str(e)}")
        except Exception as e:
            await inter.edit_original_message(f"⚠️ Ошибка при обработке инвентаря: {str(e)}")


def setup(bot):
    bot.add_cog(InventoryCog(bot))