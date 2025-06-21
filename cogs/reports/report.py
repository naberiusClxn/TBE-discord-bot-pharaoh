import disnake
from disnake.ext import commands, tasks
from disnake import Embed, PermissionOverwrite
import io
import sqlite3
import datetime
from config import ticket_category_id, created_reports_role_id, moderation_role_id, report_role_id


class ReportCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.init_db()
        self.check_expired_roles.start()

    def init_db(self):
        self.conn = sqlite3.connect('reports.db')
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS role_timers (
            user_id INTEGER PRIMARY KEY,
            role_end_time TEXT,
            channel_id INTEGER
        )
        ''')
        self.conn.commit()

    @tasks.loop(minutes=1)
    async def check_expired_roles(self):
        now = datetime.datetime.utcnow()
        self.cursor.execute('SELECT user_id, channel_id FROM role_timers WHERE role_end_time <= ?', (now.isoformat(),))
        expired = self.cursor.fetchall()

        for record in expired:
            user_id, channel_id = record
            for guild in self.bot.guilds:
                member = guild.get_member(user_id)
                if member:
                    if report_role_id in [r.id for r in member.roles]:
                        role = guild.get_role(report_role_id)
                        if role:
                            try:
                                await member.remove_roles(role, reason="Время действия роли истекло")
                            except disnake.HTTPException:
                                pass

                    self.cursor.execute('DELETE FROM role_timers WHERE user_id = ?', (user_id,))
                    self.conn.commit()

                    channel = guild.get_channel(channel_id)
                    if channel:
                        try:
                            await channel.delete(reason="Тикет закрыт по истечении времени")
                        except disnake.HTTPException:
                            pass
                    break

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Ког {self.__class__.__name__} готов')

    @commands.slash_command(description="Создать отчет")
    async def report(
            self,
            inter: disnake.ApplicationCommandInteraction,
            image1: disnake.Attachment = commands.Param(..., description="Обязательное изображение"),
            image2: disnake.Attachment = None,
            image3: disnake.Attachment = None,
            image4: disnake.Attachment = None,
            image5: disnake.Attachment = None,
    ):
        if not any(role.id in created_reports_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        await inter.response.defer(ephemeral=True)

        category = self.bot.get_channel(ticket_category_id)
        if not category or not isinstance(category, disnake.CategoryChannel):
            return await inter.followup.send("Категория для тикетов не найдена.", ephemeral=True)

        overwrites = {
            inter.guild.default_role: PermissionOverwrite(read_messages=False),
            inter.author: PermissionOverwrite(read_messages=True),
        }

        for role_id in moderation_role_id:
            role = inter.guild.get_role(role_id)
            if role:
                overwrites[role] = PermissionOverwrite(read_messages=True)

        ticket_channel = await category.create_text_channel(
            name=f"report-{inter.user.name}",
            reason=f"Отчёт от {inter.user}",
            overwrites=overwrites
        )

        main_embed = Embed(
            description=(
                f"После нажатия на ✅, пользователю {inter.user.mention} выдается заранее настроенная временная роль (например, @Активный).\n\n"
                "Эта роль автоматически удаляется через 24 часов по МСК.\n\n"
            ),
            color=disnake.Color.blue()
        )
        main_embed.set_author(name=f"Отчёт от {inter.user}", icon_url=inter.user.display_avatar.url)

        embeds = [main_embed]

        images = [img for img in [image1, image2, image3, image4, image5] if img]
        for img in images:
            try:
                await img.save(io.BytesIO())
                image_url = img.url

                image_embed = Embed(color=disnake.Color.blurple())
                image_embed.set_image(url=image_url)
                embeds.append(image_embed)
            except Exception as e:
                print(f"Ошибка при обработке изображения: {e}")
                continue

        view = disnake.ui.View(timeout=None)
        approve_button = disnake.ui.Button(
            style=disnake.ButtonStyle.success,
            emoji="✅",
            custom_id=f"approve_report_{inter.user.id}_{ticket_channel.id}"
        )
        view.add_item(approve_button)

        await ticket_channel.send(embeds=embeds, view=view)

        self.cursor.execute('INSERT OR REPLACE INTO role_timers (user_id, channel_id) VALUES (?, ?)',
                            (inter.user.id, ticket_channel.id))
        self.conn.commit()

        await inter.followup.send(f"Отчёт успешно создан: {ticket_channel.mention}", ephemeral=True)

    @commands.Cog.listener()
    async def on_button_click(self, inter: disnake.MessageInteraction):
        if not inter.component.custom_id.startswith("approve_report_"):
            return

        if not any(role.id in moderation_role_id for role in inter.user.roles):
            await inter.response.send_message("У вас нет прав для выполнения этого действия.", ephemeral=True)
            return

        try:
            _, _, user_id_str, channel_id_str = inter.component.custom_id.split('_')
            user_id = int(user_id_str)
            channel_id = int(channel_id_str)
        except ValueError:
            return

        member = inter.guild.get_member(user_id)
        if not member:
            await inter.response.send_message("Пользователь не найден.", ephemeral=True)
            return

        role = inter.guild.get_role(report_role_id)
        if not role:
            await inter.response.send_message("Роль для выдачи не найдена.", ephemeral=True)
            return

        end_time = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

        self.cursor.execute('SELECT role_end_time FROM role_timers WHERE user_id = ?', (user_id,))
        existing = self.cursor.fetchone()

        if existing and existing[0]:
            try:
                current_end = datetime.datetime.fromisoformat(existing[0])
                new_end = current_end + datetime.timedelta(hours=24)
                end_time = new_end
                action = "продлена"
            except (TypeError, ValueError):
                action = "выдана"
        else:
            action = "выдана"

        try:
            await member.add_roles(role, reason=f"Роль выдана/продлена модератором {inter.user}")
        except disnake.HTTPException:
            await inter.response.send_message("Не удалось выдать роль.", ephemeral=True)
            return

        self.cursor.execute('''
        INSERT OR REPLACE INTO role_timers (user_id, role_end_time, channel_id) 
        VALUES (?, ?, ?)
        ''', (user_id, end_time.isoformat(), channel_id))
        self.conn.commit()

        channel = inter.guild.get_channel(channel_id)
        if channel:
            try:
                await channel.delete(reason="Тикет закрыт модератором")
            except disnake.HTTPException:
                pass

        await inter.response.send_message(
            f"Роль {role.mention} {action} пользователю {member.mention} до {end_time.strftime('%Y-%m-%d %H:%M')} UTC. Канал удален.",
            ephemeral=True
        )

    def cog_unload(self):
        self.check_expired_roles.cancel()
        self.conn.close()


def setup(bot):
    bot.add_cog(ReportCog(bot))