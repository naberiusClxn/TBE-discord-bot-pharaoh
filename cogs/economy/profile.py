import disnake
from disnake.ext import commands
import sqlite3
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from main import bat_icon, font_path
from config import admin_status, moderation_role_id, curator


class ProfileCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.mecenat_image_path = "images/market/mecenat.png"
        self.helper = "images/status/helper.png"
        self.admin = "images/status/admin.png"
        self.curator = "images/status/curator.png"
        self.token_images = {
            3: "images/status/3.png",
            5: "images/status/5.png",
            10: "images/status/10.png",
            15: "images/status/15.png",
            25: "images/status/25.png",
            40: "images/status/40.png",
            50: "images/status/50.png",
            75: "images/status/75.png",
            100: "images/status/100.png"
        }

    def has_mecenat(self, user_id: str, guild_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM purchases
            WHERE user_id = ? AND guild_id = ? AND item_name = 'Меценат'
        """, (user_id, guild_id))
        result = cursor.fetchone()[0]
        conn.close()
        return result > 0

    def get_status_image(self, user: disnake.Member, user_id: str, guild_id: str) -> str:
        user_role_ids = {role.id for role in user.roles}

        admin_roles = {admin_status}
        mod_roles = set(moderation_role_id)
        curator_roles = set(curator)

        if user_role_ids & admin_roles:
            return self.admin
        if user_role_ids & curator_roles:
            return self.curator
        if user_role_ids & mod_roles:
            return self.helper
        if self.has_mecenat(user_id, guild_id):
            return self.mecenat_image_path

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM punishments 
            WHERE user_id = ? AND guild_id = ? AND type = 'TOKEN'
        """, (user_id, guild_id))
        token_count = cursor.fetchone()[0]
        conn.close()

        for token_threshold, image_path in sorted(self.token_images.items(), reverse=True):
            if token_count >= token_threshold:
                return image_path

        return bat_icon

    @commands.slash_command(description="Посмотреть профиль пользователя")
    async def profile(self, inter: disnake.ApplicationCommandInteraction, user: disnake.Member = None):
        user = user or inter.author
        user_id = str(user.id)
        guild_id = str(inter.guild.id)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*) FROM punishments 
            WHERE user_id = ? AND guild_id = ? AND type = 'TOKEN'
        """, (user_id, guild_id))
        token_count = cursor.fetchone()[0]

        cursor.execute("""
            SELECT balance, voice_hours FROM balances
            WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id))
        balance_result = cursor.fetchone()
        balance = balance_result[0] if balance_result else 0
        voice_hours = balance_result[1] if balance_result else 0

        cursor.execute("""
            SELECT user_id, COUNT(*) as token_count 
            FROM punishments 
            WHERE type = 'TOKEN' 
            GROUP BY user_id 
            ORDER BY token_count DESC
        """)
        all_users_tokens = cursor.fetchall()

        top_position = 0
        for idx, (top_user_id, _) in enumerate(all_users_tokens, start=1):
            if top_user_id == user_id:
                top_position = idx
                break

        conn.close()

        self.image_path = self.get_status_image(user, user_id, guild_id)

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
        draw.text((x + 390, y + 267), text, font=font)

        balance_text = f"{balance}"
        draw.text((x - 450, y + 267), balance_text, font=font)

        voice_hours_text = f"{voice_hours}"
        draw.text((x - 110, y + 267), voice_hours_text, font=font)

        top_text = f"#{top_position}"
        draw.text((x - 50, y + 350), top_text, font=font)

        nick = user.nick if user.nick else user.name
        nick_text = f"{nick}"
        nick_bbox = font.getbbox(nick_text)
        nick_text_width = nick_bbox[2] - nick_bbox[0]
        nick_x = (width - nick_text_width) / 2
        draw.text((nick_x, y), nick_text, font=font)

        img_bytes = BytesIO()
        image.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        file = disnake.File(img_bytes, filename="profile.png")

        await inter.response.send_message(ephemeral=True, file=file)

def setup(bot):
    bot.add_cog(ProfileCog(bot))
