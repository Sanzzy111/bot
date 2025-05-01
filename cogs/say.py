import discord
from discord.ext import commands

COLOR_OPTIONS = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "yellow": discord.Color.gold(),
    "purple": discord.Color.purple(),
    "orange": discord.Color.orange(),
    "grey": discord.Color.greyple(),
    "default": discord.Color.default()
}

class Say(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="say", description="Send a message to a channel.")
    @discord.app_commands.describe(channel="Target channel (optional)", message="Message to send")
    async def say(self, interaction: discord.Interaction, message: str, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        await target_channel.send(message)

        embed = discord.Embed(
            title="✅ Message Sent",
            description=f"Sent to {target_channel.mention}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.app_commands.command(name="say_embed", description="Send an embed to a channel.")
    @discord.app_commands.describe(
        channel="Target channel (optional)",
        title="Embed title",
        description="Embed description",
        color="Embed color (red, blue, green, yellow, purple, orange, grey, default)",
        image_url="Optional image URL",
        image_position="Where to put the image (top=thumbnail, bottom=image)"
    )
    async def say_embed(self, interaction: discord.Interaction, title: str, description: str, color: str = "default", image_url: str = None, image_position: str = "bottom", channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission to use this command.", ephemeral=True)
            return

        embed_color = COLOR_OPTIONS.get(color.lower(), discord.Color.default())
        embed = discord.Embed(title=title, description=description, color=embed_color)

        if image_url:
            if image_position.lower() == "top":
                embed.set_thumbnail(url=image_url)
            else:
                embed.set_image(url=image_url)

        await interaction.response.defer(thinking=True, ephemeral=True)
        await target_channel.send(embed=embed)

        confirm_embed = discord.Embed(
            title="✅ Embed Sent",
            description=f"Embed sent to {target_channel.mention}",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Say(bot))