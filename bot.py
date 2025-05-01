import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        
        # Tentukan owner bot (ganti dengan ID Discord Anda)
        owner_ids = [1194983217086857292]  # Contoh: [your_discord_id]
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=os.getenv('APPLICATION_ID'),
            owner_ids=owner_ids  # Tambahkan ini
        )

    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                await self.load_extension(f'cogs.{filename[:-3]}')
        
        # Sync slash commands
        await self.tree.sync()

        # Tambahkan command sync manual
        @self.command()
        @commands.is_owner()  # Hanya owner yang bisa jalankan
        async def sync(ctx):
            """Sync slash commands (Owner only)"""
            await self.tree.sync()
            await ctx.send("✅ Slash commands synced!", ephemeral=True)

bot = MyBot()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

if __name__ == '__main__':
    from utils.keep_alive import keep_alive
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))