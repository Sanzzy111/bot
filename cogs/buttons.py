import discord
from discord.ext import commands
from discord import app_commands
import re

class Buttons(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, member):
        return member.guild_permissions.administrator or member == member.guild.owner or member.bot

    @app_commands.command(name="multibutton", description="Admin-only: Buat pesan dengan beberapa tombol link")
    @app_commands.describe(
        message="Pesan yang akan ditampilkan di atas tombol",
        button1_label="Label untuk tombol 1",
        button1_url="URL untuk tombol 1",
        button2_label="Label untuk tombol 2 (opsional)",
        button2_url="URL untuk tombol 2 (opsional)",
        button3_label="Label untuk tombol 3 (opsional)",
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

        # Parse emoji from label if exists
        emoji_pattern = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]+):(?P<id>[0-9]+)>'
        emoji_match = re.search(emoji_pattern, button1_label)

        if emoji_match:
            emoji_id = int(emoji_match.group('id'))
            emoji = discord.PartialEmoji(name=emoji_match.group('name'), id=emoji_id, animated=bool(emoji_match.group('animated')))
            clean_label = re.sub(emoji_pattern, '', button1_label).strip()
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.link,
                label=clean_label,
                emoji=emoji,
                url=button1_url
            ))
        else:
            view.add_item(discord.ui.Button(
                style=discord.ButtonStyle.link,
                label=button1_label,
                url=button1_url
            ))

        if button2_label and button2_url:
            emoji_match = re.search(emoji_pattern, button2_label)
            if emoji_match:
                emoji_id = int(emoji_match.group('id'))
                emoji = discord.PartialEmoji(name=emoji_match.group('name'), id=emoji_id, animated=bool(emoji_match.group('animated')))
                clean_label = re.sub(emoji_pattern, '', button2_label).strip()
                view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=clean_label,
                    emoji=emoji,
                    url=button2_url
                ))
            else:
                view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=button2_label,
                    url=button2_url
                ))

        if button3_label and button3_url:
            emoji_match = re.search(emoji_pattern, button3_label)
            if emoji_match:
                emoji_id = int(emoji_match.group('id'))
                emoji = discord.PartialEmoji(name=emoji_match.group('name'), id=emoji_id, animated=bool(emoji_match.group('animated')))
                clean_label = re.sub(emoji_pattern, '', button3_label).strip()
                view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=clean_label,
                    emoji=emoji,
                    url=button3_url
                ))
            else:
                view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=button3_label,
                    url=button3_url
                ))

        await interaction.channel.send(content=message, view=view)
        await interaction.followup.send("Buttons berhasil dibuat!", ephemeral=True)

    @app_commands.command(name="addbutton", description="Admin-only: Tambah multiple button ke pesan yang sudah ada")
    @app_commands.describe(
        message_link="Link pesan Discord yang ingin ditambah button",
        button1_label="Label untuk tombol 1",
        button1_url="URL untuk tombol 1",
        button2_label="Label untuk tombol 2 (opsional)",
        button2_url="URL untuk tombol 2 (opsional)",
        button3_label="Label untuk tombol 3 (opsional)",
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

            # Create new view with existing components (if any)
            view = discord.ui.View()
            if message.components:
                for action_row in message.components:
                    for component in action_row.children:
                        if isinstance(component, discord.ui.Button):
                            view.add_item(discord.ui.Button(
                                style=component.style,
                                label=component.label,
                                url=component.url
                            ))

            # Add new buttons
            emoji_pattern = r'<(?P<animated>a?):(?P<name>[a-zA-Z0-9_]+):(?P<id>[0-9]+)>'
            emoji_match = re.search(emoji_pattern, button1_label)

            if emoji_match:
                emoji_id = int(emoji_match.group('id'))
                emoji = discord.PartialEmoji(name=emoji_match.group('name'), id=emoji_id, animated=bool(emoji_match.group('animated')))
                clean_label = re.sub(emoji_pattern, '', button1_label).strip()
                view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=clean_label,
                    emoji=emoji,
                    url=button1_url
                ))
            else:
                view.add_item(discord.ui.Button(
                    style=discord.ButtonStyle.link,
                    label=button1_label,
                    url=button1_url
                ))

            if button2_label and button2_url:
                emoji_match = re.search(emoji_pattern, button2_label)
                if emoji_match:
                    emoji_id = int(emoji_match.group('id'))
                    emoji = discord.PartialEmoji(name=emoji_match.group('name'), id=emoji_id, animated=bool(emoji_match.group('animated')))
                    clean_label = re.sub(emoji_pattern, '', button2_label).strip()
                    view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=clean_label,
                        emoji=emoji,
                        url=button2_url
                    ))
                else:
                    view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=button2_label,
                        url=button2_url
                    ))

            if button3_label and button3_url:
                emoji_match = re.search(emoji_pattern, button3_label)
                if emoji_match:
                    emoji_id = int(emoji_match.group('id'))
                    emoji = discord.PartialEmoji(name=emoji_match.group('name'), id=emoji_id, animated=bool(emoji_match.group('animated')))
                    clean_label = re.sub(emoji_pattern, '', button3_label).strip()
                    view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=clean_label,
                        emoji=emoji,
                        url=button3_url
                    ))
                else:
                    view.add_item(discord.ui.Button(
                        style=discord.ButtonStyle.link,
                        label=button3_label,
                        url=button3_url
                    ))

            await message.edit(view=view)
            await interaction.followup.send("Button berhasil ditambahkan ke pesan!", ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"Gagal menambahkan button: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Buttons(bot))