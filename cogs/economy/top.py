import disnake
from disnake.ext import commands
import sqlite3


class TopCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"

    def get_logs_word_form(self, count: int) -> str:
        count = abs(count) % 100
        if 11 <= count <= 19:
            return "логов"

        match count % 10:
            case 1:
                return "лог"
            case 2 | 3 | 4:
                return "лога"
            case _:
                return "логов"


    def get_hours_word_form(self, count: int) -> str:
        count = abs(count) % 100
        if 11 <= count <= 19:
            return "часов"

        match count % 10:
            case 1:
                return "час"
            case 2 | 3 | 4:
                return "часа"
            case _:
                return "часов"


    @commands.slash_command(description="Показать топ пользователей с наибольшим количеством логов")
    async def top(self, inter: disnake.ApplicationCommandInteraction):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, COUNT(*) as token_count 
            FROM punishments 
            WHERE type = 'TOKEN' 
            GROUP BY user_id 
            ORDER BY token_count DESC 
            LIMIT 10
        """)

        top_users = cursor.fetchall()
        conn.close()

        if not top_users:
            await inter.response.send_message("Топ пользователей с логами пуст.", ephemeral=True)
            return

        top_list = ""
        for idx, (user_id, token_count) in enumerate(top_users, start=1):
            user = await self.bot.fetch_user(user_id)
            word_form = self.get_logs_word_form(token_count)
            top_list += f"{idx}. {user.mention} - {token_count} {word_form}\n"

        embed = disnake.Embed(
            title="Топ пользователей с наибольшим количеством логов",
            description=top_list,
            color=disnake.Color.blue()
        )
        await inter.response.send_message(embed=embed)

    @commands.slash_command(description="Показать топ пользователей с наибольшим временем в голосовых каналах")
    async def vtop(self, inter: disnake.ApplicationCommandInteraction):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, voice_hours 
            FROM balances 
            ORDER BY voice_hours DESC 
            LIMIT 10
        """)

        top_users = cursor.fetchall()
        conn.close()

        if not top_users:
            await inter.response.send_message("Топ пользователей по голосовым часам пуст.", ephemeral=True)
            return

        top_list = ""
        for idx, (user_id, voice_hours) in enumerate(top_users, start=1):
            user = await self.bot.fetch_user(int(user_id))
            word_form = self.get_hours_word_form(voice_hours)
            top_list += f"{idx}. {user.mention} - {voice_hours} {word_form}\n"


        embed = disnake.Embed(
            title="Топ пользователей по голосовым часам",
            description=top_list,
            color=disnake.Color.green()
        )
        await inter.response.send_message(embed=embed)



def setup(bot):
    bot.add_cog(TopCog(bot))
