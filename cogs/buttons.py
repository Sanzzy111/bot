import discord
from discord.ext import commands
from discord import app_commands
import re
import aiohttp
from io import BytesIO

class Buttons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def is_admin(self, member):
        return member.guild_permissions.administrator or member == member.guild.owner or member.bot

    async def create_button(self, label: str, url: str):
        """Helper function to create button with emoji or image"""
        # Check if label contains emoji
        emoji_pattern = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]+):(?P<id>[0-9]+)>'
        emoji_match = re.search(emoji_pattern, label)
        
        # Check if label is image URL
        is_image_url = re.match(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+\.(?:png|jpg|jpeg|gif)', label.strip())

        if emoji_match:
            # Handle server emoji
            emoji_id = int(emoji_match.group('id'))
            emoji = discord.PartialEmoji(
                name=emoji_match.group('name'),
                id=emoji_id,
                animated=bool(emoji_match.group('animated'))
            )
            clean_label = re.sub(emoji_pattern, '', label).strip()
            return discord.ui.Button(
                style=discord.ButtonStyle.link,
                label=clean_label,
                emoji=emoji,
                url=url
            )
        elif is_image_url:
            # Handle image URL
            try:
                async with self.session.get(label) as resp:
                    if resp.status == 200:
                        image_data = await resp.read()
                        emoji = await self._create_temp_emoji(label, image_data)
                        return discord.ui.Button(
                            style=discord.ButtonStyle.link,
                            label=" ",  # Empty label for image-only button
                            emoji=emoji,
                            url=url
                        )
            except Exception:
                pass
        
        # Default text button
        return discord.ui.Button(
            style=discord.ButtonStyle.link,
            label=label,
            url=url
        )

    async def _create_temp_emoji(self, image_url: str, image_data: bytes):
        """Try to create temporary emoji from image (fallback to default if failed)"""
        try:
            # For demo purposes, we'll use PartialEmoji with the URL as name
            # In production, you'd want to actually upload the emoji if bot has permissions
            return discord.PartialEmoji(name=image_url.split('/')[-1], url=image_url)
        except:
            return "🔗"  # Fallback emoji

    @app_commands.command(name="multibutton", description="Admin-only: Buat pesan dengan beberapa tombol link")
    @app_commands.describe(
        message="Pesan yang akan ditampilkan di atas tombol",
        button1_label="Label/Emoji/Image URL untuk tombol 1",
        button1_url="URL untuk tombol 1",
        button2_label="Label/Emoji/Image URL untuk tombol 2 (opsional)",
        button2_url="URL untuk tombol 2 (opsional)",
        button3_label="Label/Emoji/Image URL untuk tombol 3 (opsional)",
        button3_url="URL untuk tombol 3 (opsional)"
    )
    async def create_multibutton(
        self,
        interaction: discord.Interaction,
        message: str,
        button1_label: str,
        button1_url: str,
        button2_label: str = None,
        button2_url: str = None,
        button3_label: str = None,
        button3_url: str = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("Kamu tidak punya izin untuk menggunakan perintah ini.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        view = discord.ui.View()

        # Add buttons
        buttons = [
            (button1_label, button1_url),
            (button2_label, button2_url) if button2_label and button2_url else None,
            (button3_label, button3_url) if button3_label and button3_url else None
        ]

        for btn in filter(None, buttons):
            label, url = btn
            button = await self.create_button(label, url)
            view.add_item(button)

        await interaction.channel.send(content=message, view=view)
        await interaction.followup.send("Buttons berhasil dibuat!", ephemeral=True)

    @app_commands.command(name="addbutton", description="Admin-only: Tambah multiple button ke pesan yang sudah ada")
    @app_commands.describe(
        message_link="Link pesan Discord yang ingin ditambah button",
        button1_label="Label/Emoji/Image URL untuk tombol 1",
        button1_url="URL untuk tombol 1",
        button2_label="Label/Emoji/Image URL untuk tombol 2 (opsional)",
        button2_url="URL untuk tombol 2 (opsional)",
        button3_label="Label/Emoji/Image URL untuk tombol 3 (opsional)",
        button3_url="URL untuk tombol 3 (opsional)"
    )
    async def add_button(
        self,
        interaction: discord.Interaction,
        message_link: str,
        button1_label: str,
        button1_url: str,
        button2_label: str = None,
        button2_url: str = None,
        button3_label: str = None,
        button3_url: str = None
    ):
        if not self.is_admin(interaction.user):
            await interaction.response.send_message("Kamu tidak punya izin untuk menggunakan perintah ini.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        # Parse message link
        pattern = r"https://discord.com/channels/(\d+)/(\d+)/(\d+)"
        match = re.match(pattern, message_link)

        if not match:
            await interaction.followup.send("Link pesan tidak valid! Gunakan format: https://discord.com/channels/server_id/channel_id/message_id", ephemeral=True)
            return

        guild_id, channel_id, message_id = map(int, match.groups())

        try:
            channel = self.bot.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            view = discord.ui.View()
            if message.components:
                for action_row in message.components:
                    for component in action_row.children:
                        if isinstance(component, discord.ui.Button):
                            view.add_item(component)

            # Add new buttons
            buttons = [
                (button1_label, button1_url),
                (button2_label, button2_url) if button2_label and button2_url else None,
                (button3_label, button3_url) if button3_label and button3_url else None
            ]

            for btn in filter(None, buttons):
                label, url = btn
                button = await self.create_button(label, url)
                view.add_item(button)

            await message.edit(view=view)
            await interaction.followup.send("Button berhasil ditambahkan ke pesan!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"Gagal menambahkan button: {str(e)}", ephemeral=True)

    def cog_unload(self):
        self.bot.loop.create_task(self.session.close())

async def setup(bot):
    await bot.add_cog(Buttons(bot))