import discord
from discord.ext import commands

class Protec(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.owner_id = 1194983217086857292  # Ganti dengan ID kamu

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        inviter = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                inviter = entry.user
                break
        except:
            pass

        if not inviter or inviter.id != self.owner_id:
            try:
                channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
                if channel:
                    await channel.send("Maaf, hanya owner yang boleh invite saya. Saya akan keluar.")
            except:
                pass
            await guild.leave()

async def setup(bot):
    await bot.add_cog(Protec(bot))