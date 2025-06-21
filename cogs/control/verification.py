import disnake
from disnake.ext import commands
import random

from config import verification_role_id


class VerificationStartView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VerificationStartButton())

class VerificationStartButton(disnake.ui.Button):
    def __init__(self):
        super().__init__(label="Пройти верификацию", style=disnake.ButtonStyle.primary, custom_id="verification_start")

    async def callback(self, interaction: disnake.MessageInteraction):
        view = VerificationCodeView()
        image_url = view.generate_captcha()
        await interaction.response.send_message(
            "🔍 Для прохождения верификации выберите правильное число:",
            embed=disnake.Embed().set_image(url=image_url),
            view=view,
            ephemeral=True
        )

class VerificationCodeView(disnake.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.correct_code = random.randint(1000, 9999)
        self.color = random.choice(["0xff7f50", "0x800000", "0x8b4513", "0xff0000", "0xc71585", "0x009933", "0xccff66"])
        self.turn = random.randint(-27, 26)
        self.size = random.randint(38, 67)
        self.add_buttons()

    def generate_captcha(self):
        url = (
            f"https://imgenx.vercel.app/img?s=400x200&fill=0x303030"
            f"&l=txt:{self.correct_code};x:194,y:102,s:{self.size},r:{self.turn},o:cm,lh:16,bw:1,w:300,bc:0x666666,c:{self.color}"
        )
        return url

    def add_buttons(self):
        correct_position = random.randint(0, 3)
        incorrect_codes = random.sample(range(1000, 9999), 3)

        for i in range(4):
            if i == correct_position:
                self.add_item(VerificationButton(label=str(self.correct_code), correct=True))
            else:
                self.add_item(VerificationButton(label=str(incorrect_codes.pop()), correct=False))

class VerificationButton(disnake.ui.Button):
    def __init__(self, label: str, correct: bool):
        super().__init__(label=label, style=disnake.ButtonStyle.secondary)
        self.correct = correct

    async def callback(self, interaction: disnake.MessageInteraction):
        member = interaction.user
        guild = interaction.guild

        if self.correct:
            await member.add_roles(guild.get_role(verification_role_id), reason="Верификация пройдена")
            await interaction.response.send_message("**Вы успешно прошли верификацию.**", ephemeral=True)
        else:
            await interaction.response.send_message("**Простите, вы не прошли верификацию. Попробуйте ещё раз.**", ephemeral=True)

class VerificationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(VerificationStartView())
        print("✅ Verification view registered!")

    @commands.slash_command(description="Создать сообщение для верификации")
    async def ver(self, inter: disnake.ApplicationCommandInteraction):
        if not inter.author.guild_permissions.administrator:
            await inter.response.send_message("У вас нет доступа к этой команде.", ephemeral=True)
            return

        embed = disnake.Embed(
            description="## Верификация\nПройдите верификацию, чтобы получить доступ к каналам.",
            color=disnake.Color.red()
        )
        await inter.channel.send(embed=embed, view=VerificationStartView())
        await inter.response.send_message("✅ Сообщение с верификацией отправлено", ephemeral=True)

def setup(bot):
    bot.add_cog(VerificationCog(bot))

