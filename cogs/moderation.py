import discord
from discord.ext import commands
from discord import option
from datetime import datetime, timedelta
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ====== MUTE ======
    @commands.slash_command(description="Mute a user for a specific time")
    @option("user", discord.Member, description="User to mute")
    @option("duration", str, description="Duration (e.g., 10s, 5m, 2h)")
    async def mute(self, ctx, user: discord.Member, duration: str):
        await ctx.defer()
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted")

            for channel in ctx.guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)

        if muted_role in user.roles:
            return await ctx.respond("User is already muted.")

        await user.add_roles(muted_role)
        await ctx.respond(f"{user.mention} has been muted for {duration}")

        time_multiplier = {"s": 1, "m": 60, "h": 3600}
        unit = duration[-1]
        if unit not in time_multiplier:
            return await ctx.respond("Invalid time format! Use s, m, or h.")
        try:
            time_amount = int(duration[:-1])
        except ValueError:
            return await ctx.respond("Invalid number format in duration.")
        
        seconds = time_amount * time_multiplier[unit]
        await asyncio.sleep(seconds)

        if muted_role in user.roles:
            await user.remove_roles(muted_role)
            try:
                await user.send(f"You have been unmuted in {ctx.guild.name}.")
            except:
                pass

    # ====== UNMUTE ======
    @commands.slash_command(description="Unmute a user")
    @option("user", discord.Member, description="User to unmute")
    async def unmute(self, ctx, user: discord.Member):
        muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
        if muted_role and muted_role in user.roles:
            await user.remove_roles(muted_role)
            await ctx.respond(f"{user.mention} has been unmuted.")
        else:
            await ctx.respond("User is not muted.")

    # ====== BAN ======
    @commands.slash_command(description="Ban a user from the server")
    @option("user", discord.Member, description="User to ban")
    @option("reason", str, description="Reason for ban", required=False)
    async def ban(self, ctx, user: discord.Member, reason: str = "No reason provided"):
        await ctx.guild.ban(user, reason=reason)
        await ctx.respond(f"{user} has been banned. Reason: {reason}")

    # ====== UNBAN ======
    @commands.slash_command(description="Unban a user from the server")
    @option("user_id", str, description="User ID to unban")
    async def unban(self, ctx, user_id: str):
        user_id = int(user_id)
        banned_users = await ctx.guild.bans()
        for entry in banned_users:
            if entry.user.id == user_id:
                await ctx.guild.unban(entry.user)
                return await ctx.respond(f"Unbanned {entry.user}")
        await ctx.respond("User not found in ban list.")

    # ====== KICK ======
    @commands.slash_command(description="Kick a user from the server")
    @option("user", discord.Member, description="User to kick")
    @option("reason", str, description="Reason for kick", required=False)
    async def kick(self, ctx, user: discord.Member, reason: str = "No reason provided"):
        await ctx.guild.kick(user, reason=reason)
        await ctx.respond(f"{user} has been kicked. Reason: {reason}")

def setup(bot):
    bot.add_cog(Moderation(bot))
