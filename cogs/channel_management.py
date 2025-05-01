import discord
from discord import app_commands
from discord.ext import commands

class ChannelManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="create_channel",
        description="Create a new text or voice channel"
    )
    @app_commands.choices(channel_type=[
        app_commands.Choice(name="text", value="text"),
        app_commands.Choice(name="voice", value="voice")
    ])
    @app_commands.default_permissions(manage_channels=True)
    async def create_channel(
        self,
        interaction: discord.Interaction,
        channel_type: app_commands.Choice[str],
        channel_name: str,
        category: discord.CategoryChannel = None
    ):
        """Create a new channel in the specified category"""
        
        try:
            if channel_type.value == "text":
                new_channel = await interaction.guild.create_text_channel(
                    name=channel_name,
                    category=category
                )
                msg = f"Text channel {new_channel.mention} created!"
            else:
                new_channel = await interaction.guild.create_voice_channel(
                    name=channel_name,
                    category=category
                )
                msg = f"Voice channel {new_channel.mention} created!"

            await interaction.response.send_message(msg, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f"Failed to create channel: {str(e)}",
                ephemeral=True
            )

    @app_commands.command(
        name="delete_channel",
        description="Delete a text or voice channel"
    )
    @app_commands.default_permissions(manage_channels=True)
    async def delete_channel(
        self,
        interaction: discord.Interaction,
        channel: discord.abc.GuildChannel
    ):
        """Delete the specified channel"""
        
        try:
            if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
                await interaction.response.send_message(
                    "You can only delete text or voice channels!",
                    ephemeral=True
                )
                return

            channel_name = channel.name
            await channel.delete()
            await interaction.response.send_message(
                f"Channel #{channel_name} deleted successfully!",
                ephemeral=True
            )

        except Exception as e:
            await interaction.response.send_message(
                f"Failed to delete channel: {str(e)}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(ChannelManagement(bot))