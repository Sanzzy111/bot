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
        
        owner_ids = [1194983217086857292]  # Ganti dengan ID Discord Anda
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=os.getenv('APPLICATION_ID'),
            owner_ids=owner_ids
        )

    async def setup_hook(self):
        # Load cogs
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    print(f'✅ Cog loaded: cogs.{filename[:-3]}')
                except Exception as e:
                    print(f'❌ Failed to load cog {filename}: {e}')
        
        # Sync slash commands globally
        await self.tree.sync()
        print('✅ Slash commands synced!')

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

# Tambahkan command sync manual di luar class
bot = MyBot()

@bot.command()
@commands.is_owner()
async def sync(ctx):
    """Sync slash commands (Owner only)"""
    await ctx.bot.tree.sync()
    await ctx.send("✅ Slash commands synced globally!", ephemeral=True)

if __name__ == '__main__':
    from utils.keep_alive import keep_alive
    keep_alive()
    
    try:
        bot.run(os.getenv('DISCORD_TOKEN'))
    except discord.LoginFailure:
        print("⚠️ Token invalid! Please check your .env file")
    except Exception as e:
        print(f"⚠️ Bot crashed: {e}")