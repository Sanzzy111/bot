import discord
from discord.ext import commands
import asyncio

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def ensure_muted_role(self, guild: discord.Guild):
        muted_role = discord.utils.get(guild.roles, name="Muted")
        if muted_role is None:
            muted_role = await guild.create_role(name="Muted", reason="To mute members.")
            for channel in guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, speak=False, add_reactions=False)
        return muted_role

    @discord.app_commands.command(name="kick", description="Kick a member from the server.")
    @discord.app_commands.describe(member="Member to kick", reason="Reason for kicking")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("You don't have permission to kick members.", ephemeral=True)
            return
        await member.kick(reason=reason)
        await interaction.response.send_message(f"Kicked {member.mention} for: {reason}")

    @discord.app_commands.command(name="ban", description="Ban a member from the server.")
    @discord.app_commands.describe(member="Member to ban", reason="Reason for banning")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)
            return
        await member.ban(reason=reason)
        await interaction.response.send_message(f"Banned {member.mention} for: {reason}")

    @discord.app_commands.command(name="clear", description="Clear a specific number of messages from the channel.")
    @discord.app_commands.describe(amount="How many messages you want to delete (1-100)")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission to manage messages.", ephemeral=True)
            return
        if amount < 1 or amount > 100:
            await interaction.response.send_message("Please specify an amount between 1 and 100.", ephemeral=True)
            return
        await interaction.response.defer()
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"Cleared {len(deleted)} messages!", ephemeral=True)

    @discord.app_commands.command(name="mute", description="Mute a member for a certain amount of time (in seconds).")
    @discord.app_commands.describe(member="Member to mute", duration="Duration to mute in seconds", reason="Reason for muting")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You don't have permission to mute members.", ephemeral=True)
            return
        muted_role = await self.ensure_muted_role(interaction.guild)

        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"Muted {member.mention} for {duration} seconds.", ephemeral=True)

        await asyncio.sleep(duration)
        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Mute duration expired")

    @discord.app_commands.command(name="unmute", description="Unmute a muted member manually.")
    @discord.app_commands.describe(member="Member to unmute")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You don't have permission to unmute members.", ephemeral=True)
            return
        muted_role = await self.ensure_muted_role(interaction.guild)

        if muted_role in member.roles:
            await member.remove_roles(muted_role, reason="Manual unmute")
            await interaction.response.send_message(f"Unmuted {member.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{member.mention} is not muted.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))