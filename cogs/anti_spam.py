import discord
from discord.ext import commands
from discord import app_commands, Embed
import re, datetime, asyncio
from collections import defaultdict

spam_tracker = defaultdict(lambda: {"messages": [], "warnings": 0})
emoji_spam_limit = 4
emoji_mute_duration = 2       
mention_mute_duration = 4     
spam_timeout = 10             
mention_limit = 5

def extract_emojis(text):
    return re.findall(r'<a?:\w+:\d+>|[\U00010000-\U0010ffff]', text)

def count_mentions(message):
    return len(message.mentions)

async def apply_mute(member, duration, reason="Spam"):
    mute_role = discord.utils.get(member.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await member.guild.create_role(name="Muted")
        for channel in member.guild.channels:
            await channel.set_permissions(mute_role, send_messages=False)
    await member.add_roles(mute_role, reason=reason)
    await asyncio.sleep(duration)
    await member.remove_roles(mute_role)

class Security(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.guild_permissions.administrator:
            return

        now = datetime.datetime.utcnow()
        data = spam_tracker[message.author.id]
        data["messages"] = [t for t in data["messages"] if (now - t).seconds < 5]
        data["messages"].append(now)

        if len(data["messages"]) > 3:
            await message.delete()
            data["warnings"] += 1

            if data["warnings"] == 1:
                embed = Embed(title="Peringatan Spam", description=f"{message.author.mention}, jangan spam!", color=discord.Color.orange())
                await message.channel.send(embed=embed, delete_after=5)
            else:
                embed = Embed(
                    title="Mute Diterapkan",
                    description=f"{message.author.mention} telah dimute karena spam selama {spam_timeout // 60} menit!",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=5)
                await apply_mute(message.author, spam_timeout)
            return

        emoji_count = len(extract_emojis(message.content))
        if emoji_count > emoji_spam_limit:
            await message.delete()
            embed = Embed(
                title="Terlalu Banyak Emoji",
                description=f"{message.author.mention}, terlalu banyak emoji dalam satu pesan! Dimute selama {emoji_mute_duration} detik.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=5)
            await apply_mute(message.author, emoji_mute_duration)
            return

        mention_count = count_mentions(message)
        if mention_count > mention_limit:
            await message.delete()
            embed = Embed(
                title="Terlalu Banyak Mention",
                description=f"{message.author.mention}, kamu menyebut terlalu banyak anggota! Dimute selama {mention_mute_duration // 60} menit.",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed, delete_after=5)
            await apply_mute(message.author, mention_mute_duration)
            return

async def setup(bot):
    await bot.add_cog(Security(bot))
