import discord
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
import io
import json
import os

CONFIG_FILE = "welcome_config.json"

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "w") as f:
                json.dump({}, f)

    def save_config(self, data):
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def load_config(self):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

    def generate_welcome_image(self, member, background_path):
        try:
            base = Image.open(background_path).convert("RGBA")
        except Exception as e:
            print(f"Gagal buka background: {e}")
            return None

        # Blur background
        base = base.filter(ImageFilter.GaussianBlur(radius=2))

        draw = ImageDraw.Draw(base)

        # Load fonts
        try:
            font_large = ImageFont.truetype("fonts/Road_Rage.otf", 50)
            font_small = ImageFont.truetype("fonts/Road_Rage.otf", 30)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        # Setup Text
        text1 = "WELCOME"
        text2 = str(member.name).upper()

        text1_width = draw.textlength(text1, font=font_large)
        text2_width = draw.textlength(text2, font=font_small)

        # Colors
        shadow_color = "black"
        main_color = (186, 85, 211)  # Light Purple

        # Draw WELCOME Text + Shadow
        draw.text(((base.width - text1_width) / 2 + 2, base.height - 170 + 2), text1, font=font_large, fill=shadow_color)
        draw.text(((base.width - text1_width) / 2, base.height - 170), text1, font=font_large, fill=main_color)

        # Draw Username + Shadow
        draw.text(((base.width - text2_width) / 2 + 2, base.height - 100 + 2), text2, font=font_small, fill=shadow_color)
        draw.text(((base.width - text2_width) / 2, base.height - 100), text2, font=font_small, fill="white")

        # Avatar Processing
        avatar_asset = member.display_avatar.replace(size=128)
        avatar_bytes = requests.get(avatar_asset.url).content
        avatar_image = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        avatar_image = avatar_image.resize((100, 100))

        # Mask Avatar
        mask = Image.new("L", avatar_image.size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, avatar_image.size[0], avatar_image.size[1]), fill=255)
        avatar_image.putalpha(mask)

        avatar_position = ((base.width - 100) // 2, base.height - 300)

        # Glow Effect
        glow = avatar_image.copy().resize((120, 120))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=10))
        base.paste(glow, (avatar_position[0]-10, avatar_position[1]-10), glow)

        # Paste Avatar
        base.paste(avatar_image, avatar_position, avatar_image)

        # Save to bytes
        img_bytes = io.BytesIO()
        base.save(img_bytes, format="PNG")
        img_bytes.seek(0)
        return img_bytes

    @commands.Cog.listener()
    async def on_member_join(self, member):
        config = self.load_config()
        guild_id = str(member.guild.id)

        if guild_id not in config:
            return

        channel_id = config[guild_id].get("channel_id")
        background_path = config[guild_id].get("background_path")

        if channel_id and background_path:
            channel = self.bot.get_channel(channel_id)
            if channel:
                image = self.generate_welcome_image(member, background_path)
                if image:
                    file = discord.File(fp=image, filename="welcome.png")
                    embed = discord.Embed(
                        title=f"Selamat Datang, {member.name}!",
                        description=f"Selamat bergabung di **{member.guild.name}**.\nSemoga {member.mention} betah di sini!",
                        color=discord.Color.from_rgb(186, 85, 211)  # Light Purple
                    )
                    embed.set_image(url="attachment://welcome.png")
                    embed.set_thumbnail(url=member.display_avatar.url)
                    embed.set_footer(text="Welcome to the community!", icon_url=member.guild.icon.url if member.guild.icon else None)
                    await channel.send(file=file, embed=embed)

    @app_commands.command(name="setwelcomechannel", description="Atur channel welcome.")
    async def set_welcome_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        config = self.load_config()
        guild_id = str(interaction.guild.id)

        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["channel_id"] = channel.id
        self.save_config(config)
        await interaction.response.send_message(f"Channel welcome berhasil diatur ke {channel.mention}", ephemeral=True)

    @app_commands.command(name="setwelcomeimage", description="Upload gambar latar untuk welcome.")
    async def set_welcome_image(self, interaction: discord.Interaction, image: discord.Attachment):
        if not image.content_type.startswith("image/"):
            await interaction.response.send_message("Mohon upload file gambar.", ephemeral=True)
            return

        folder = "welcome_backgrounds"
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{interaction.guild.id}.png")
        await image.save(path)

        config = self.load_config()
        guild_id = str(interaction.guild.id)

        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["background_path"] = path
        self.save_config(config)
        await interaction.response.send_message("Gambar welcome berhasil disimpan!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Welcome(bot))