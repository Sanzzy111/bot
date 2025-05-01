import discord
from discord.ext import commands

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="serverinfo", description="Display detailed information about this server.")
    async def serverinfo(self, interaction: discord.Interaction):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message("This command can only be used inside a server.", ephemeral=True)
            return

        owner = await guild.fetch_member(guild.owner_id)

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles = len(guild.roles)
        boost_level = f"Level {guild.premium_tier}" if guild.premium_tier > 0 else "No Boosts"

        embed = discord.Embed(
            title=f"🏰 Server Information: {guild.name}",
            description=(
                f"```Welcome to {guild.name}! Here's a quick look at this amazing server.```"
            ),
            color=discord.Color.purple()
        )

        # Server Icon
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="**Server Name**", value=f"`{guild.name}`", inline=True)
        embed.add_field(name="**Server ID**", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="**Owner**", value=f"{owner.mention}", inline=True)

        embed.add_field(name="**Member Count**", value=f"`{guild.member_count}` members", inline=True)
        embed.add_field(name="**Channels**", value=f"`{text_channels}` Text / `{voice_channels}` Voice", inline=True)
        embed.add_field(name="**Roles**", value=f"`{roles}` Roles", inline=True)

        embed.add_field(name="**Boost Status**", value=f"`{boost_level}`", inline=True)
        embed.add_field(name="**Created At**", value=f"<t:{int(guild.created_at.timestamp())}:F>", inline=False)

        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        await interaction.response.send_message(embed=embed, ephemeral=False)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))