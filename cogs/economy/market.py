import disnake
from disnake.ext import commands
import sqlite3


class MarketCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = "database.db"
        self.create_tables()

    def create_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                guild_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                cost INTEGER NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def update_balance(self, user_id: str, guild_id: str, amount: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO balances (user_id, guild_id, balance) VALUES (?, ?, ?) "
                       "ON CONFLICT(user_id, guild_id) DO UPDATE SET balance = balance + ?",
                       (user_id, guild_id, amount, amount))
        conn.commit()
        conn.close()

    def get_balance(self, user_id: str, guild_id: str) -> int:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM balances WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 0

    def record_purchase(self, user_id: str, guild_id: str, item_name: str, cost: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO purchases (user_id, guild_id, item_name, cost)
            VALUES (?, ?, ?, ?)
        """, (user_id, guild_id, item_name, cost))
        conn.commit()
        conn.close()

    @commands.slash_command(description="Открыть магазин товаров")
    async def market(self, inter: disnake.ApplicationCommandInteraction):
        items = {
            "1%": ("35 монет", "1percent.png", 35),
            "2%": ("60 монет", "2percent.png", 60),
            "3%": ("100 монет", "3percent.png", 100),
            "Меценат": ("500 монет", "mecenat.png", 500)
        }

        embeds = []
        files = []
        buttons = []

        for name, (price, filename, cost) in items.items():
            file = disnake.File(f"images/market/{filename}", filename=filename)
            embed = disnake.Embed(description=price)
            embed.set_author(name=name)
            embed.set_thumbnail(url=f"attachment://{filename}")

            embeds.append(embed)
            files.append(file)
            buttons.append(disnake.ui.Button(label=f"Купить {name}", style=disnake.ButtonStyle.green, custom_id=name))

        view = disnake.ui.View()
        for button in buttons:
            view.add_item(button)

        async def button_callback(interaction: disnake.MessageInteraction):
            item_name = interaction.data["custom_id"]
            cost = items[item_name][2]
            user_id = str(interaction.user.id)
            guild_id = str(interaction.guild.id)

            current_balance = self.get_balance(user_id, guild_id)

            if current_balance < cost:
                await interaction.response.send_message(
                    f"У вас недостаточно монет для покупки {item_name}! Требуется {cost} монет, а у вас {current_balance}.",
                    ephemeral=True
                )
                return

            self.update_balance(user_id, guild_id, -cost)

            self.record_purchase(user_id, guild_id, item_name, cost)

            await interaction.response.send_message(f"Вы купили {item_name} за {cost} монет!", ephemeral=True)

        for button in buttons:
            button.callback = button_callback

        await inter.response.send_message("## Купить товары", embeds=embeds, files=files, view=view, ephemeral=True)


def setup(bot):
    bot.add_cog(MarketCog(bot))
