import disnake
from disnake.ext import commands, tasks
from datetime import datetime, timedelta
from config import moderation_role_id
from main import author_icon_path

WARN_ROLES = {
    1: 1344080540839444551,
    2: 1344080696217571328,
    3: 1344080784985686037,
}

REMOVE_ROLE = 1263065491925106688
ADD_ROLE = 1276151202870198272


class WarnCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.warnings = {}
        self.warn_expirations = {}
        self.check_warns.start()

    @commands.slash_command(name="warn", description="Выдаёт предупреждение")
    async def warn(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member, duration: int,
                   reason: str = "Не указана"):
        if not any(role.id in moderation_role_id for role in inter.author.roles):
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return
        if duration <= 0:
            await inter.response.send_message("Время предупреждения должно быть больше 0 минут.", ephemeral=True)
            return

        self.warnings[member.id] = self.warnings.get(member.id, 0) + 1
        warn_count = self.warnings[member.id]
        expire_time = datetime.utcnow() + timedelta(minutes=duration)
        self.warn_expirations[member.id] = expire_time

        if warn_count in WARN_ROLES:
            warn_role = WARN_ROLES[warn_count]
            await member.add_roles(disnake.Object(id=warn_role))

        if warn_count == 3:
            await member.remove_roles(disnake.Object(id=REMOVE_ROLE))
            await member.add_roles(disnake.Object(id=ADD_ROLE))

        file = disnake.File(author_icon_path, filename="hammer.png")
        embed = disnake.Embed(
            description=f"Пользователь {member.mention} получил предупреждение {warn_count}/3. Причина: {reason}"
        )
        embed.set_author(name="Выдача наказания", icon_url=f"attachment://hammer.png")
        await inter.response.send_message(embed=embed, ephemeral=True, file=file)

    @tasks.loop(minutes=1)
    async def check_warns(self):
        now = datetime.utcnow()
        for user_id, expire_time in list(self.warn_expirations.items()):
            if now >= expire_time:
                member = await self.bot.fetch_user(user_id)
                if member:
                    warn_count = self.warnings.get(user_id, 0)
                    if warn_count in WARN_ROLES:
                        warn_role = WARN_ROLES[warn_count]
                        await member.remove_roles(disnake.Object(id=warn_role))
                    self.warnings[user_id] = max(0, warn_count - 1)
                    del self.warn_expirations[user_id]


def setup(bot):
    bot.add_cog(WarnCog(bot))
