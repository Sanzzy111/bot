import discord
from discord.ext import commands
from discord import app_commands

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        """Sync slash commands"""
        await self.bot.tree.sync()
        await ctx.send("✅ Slash commands synced globally!")

async def setup(bot):
    await bot.add_cog(AdminCog(bot))