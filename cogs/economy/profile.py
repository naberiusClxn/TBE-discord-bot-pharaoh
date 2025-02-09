import disnake
from disnake.ext import commands
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from main import bat_icon, font_path

class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.image_path = bat_icon

    @commands.slash_command(description="Посмотреть профиль пользователя")
    async def profile(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        user = user or inter.author

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM punishments 
            WHERE user_id = ? AND guild_id = ? AND type = 'TOKEN'
        """, (str(user.id), str(inter.guild.id)))

        token_count = cursor.fetchone()[0]

        cursor.execute("""
                  SELECT balance FROM balances
                  WHERE user_id = ? AND guild_id = ?
              """, (str(user.id), str(inter.guild.id)))

        balance_result = cursor.fetchone()
        balance = balance_result[0] if balance_result else 0

        conn.close()

        image = Image.open(self.image_path).convert("RGBA")
        width, height = image.size

        try:
            avatar_bytes = await user.display_avatar.read()
        except Exception as e:
            print(f"{e}")
            return

        avatar_image = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
        avatar_size = (320, 320)
        avatar_image = avatar_image.resize(avatar_size)

        mask = Image.new("L", avatar_size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_size[0], avatar_size[1]), fill=255)

        avatar_position = ((width - avatar_size[0]) // 2, (height - avatar_size[1]) // 2 - 210)
        image.paste(avatar_image, avatar_position, mask)

        image = image.convert("RGBA")
        draw = ImageDraw.Draw(image)

        font = ImageFont.truetype(font_path, 50)
        width, height = image.size
        text = str(token_count)
        text_bbox = font.getbbox(text)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        x = (width - text_width) / 2
        y = (height - text_height) / 2

        draw.text((x + 390, y + 267), text, font=font, fill="white", stroke_width=5, stroke_fill="black")

        balance_text = f"{balance}"
        draw.text((x - 450, y + 267), balance_text, font=font, fill="white", stroke_width=5, stroke_fill="black")

        img_bytes = BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        file = disnake.File(img_bytes, filename="profile.png")

        await inter.response.send_message(ephemeral=True, file=file)

def setup(bot):
    bot.add_cog(ProfileCog(bot))
