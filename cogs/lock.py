import discord
from discord.ext import commands
from discord import app_commands

class Lock(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lock", description="Mengunci channel agar @everyone tidak bisa kirim pesan.")
    @app_commands.describe(channel="Channel yang akan dikunci")
    async def lock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Kamu tidak memiliki izin untuk mengunci channel.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        perms = channel.overwrites_for(interaction.guild.default_role)
        perms.update(
            send_messages=False,
            add_reactions=False,
            attach_files=False,
            create_public_threads=False,
            create_private_threads=False
        )
        await channel.set_permissions(interaction.guild.default_role, overwrite=perms)
        await interaction.followup.send(f"Channel {channel.mention} berhasil **dikunci** untuk @everyone.", ephemeral=True)

    @app_commands.command(name="unlock", description="Membuka channel agar @everyone bisa kirim pesan.")
    @app_commands.describe(channel="Channel yang akan dibuka")
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        channel = channel or interaction.channel
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("Kamu tidak memiliki izin untuk membuka channel.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        perms = channel.overwrites_for(interaction.guild.default_role)
        perms.update(send_messages=True)
        await channel.set_permissions(interaction.guild.default_role, overwrite=perms)
        await interaction.followup.send(f"Channel {channel.mention} berhasil **dibuka kembali** untuk @everyone.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Lock(bot))