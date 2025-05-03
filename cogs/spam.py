import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import json
import os

class Spam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_control = commands.CooldownMapping.from_cooldown(5, 15.0, commands.BucketType.user)
        self.bad_words = ["anjing", "bangsat", "kontol", "memek", "jancok", "asu", "bajingan", "ngentot"]
        self.violations = {}

        if os.path.exists('data/violations.json'):
            with open('data/violations.json', 'r') as f:
                self.violations = json.load(f)
        else:
            os.makedirs('data', exist_ok=True)

    def save_violations(self):
        with open('data/violations.json', 'w') as f:
            json.dump(self.violations, f)

    async def mute_member(self, member, duration=30):
        guild = member.guild
        muted_role = discord.utils.get(guild.roles, name="Muted")

        if not muted_role:
            muted_role = await guild.create_role(name="Muted")
            for channel in guild.channels:
                await channel.set_permissions(muted_role, send_messages=False, add_reactions=False, speak=False)

        if muted_role not in member.roles:
            await member.add_roles(muted_role)
            await asyncio.sleep(duration)
            await member.remove_roles(muted_role)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        user_id = str(message.author.id)
        if user_id not in self.violations:
            self.violations[user_id] = {"spam": 0, "bad_words": 0}

        user_violations = self.violations[user_id]
        action_taken = False
        deleted = False

        content_lower = message.content.lower()
        detected_words = [word for word in self.bad_words if word in content_lower]
        if detected_words:
            user_violations["bad_words"] += 1
            await self.handle_bad_words(message, detected_words, user_violations["bad_words"])
            action_taken = True
            deleted = True

        bucket = self.spam_control.get_bucket(message)
        retry_after = bucket.update_rate_limit()
        if retry_after:
            user_violations["spam"] += 1
            await self.handle_spam(message, user_violations["spam"])
            action_taken = True
            deleted = True

        if action_taken:
            self.save_violations()

    async def handle_spam(self, message, violation_count):
        try:
            await message.delete()
        except:
            pass

        user_id = str(message.author.id)
        if violation_count >= 2:
            warning = "Kamu sudah melanggar 2x, sekarang dimute 30 detik!"
            await self.mute_member(message.author)
            self.violations[user_id]["spam"] = 0
        else:
            warning = f"Kesempatan tersisa: {2 - violation_count}x. Jangan spam lagi atau kamu akan dimute!"

        embed = discord.Embed(title="🚨 Peringatan Spam", description="Tolong jangan spam pesan!😡", color=discord.Color.red())
        embed.set_thumbnail(url="https://i.imgur.com/9wDAsyz.jpeg")
        embed.add_field(name="Pelanggaran", value=warning, inline=False)
        embed.set_footer(text="Aturan server: No spam!")

        try:
            await message.channel.send(message.author.mention, embed=embed, delete_after=15.0)
        except:
            pass

    async def handle_bad_words(self, message, detected_words, violation_count):
        try:
            await message.delete()
        except:
            pass

        user_id = str(message.author.id)
        if violation_count >= 2:
            warning = "Kamu sudah 2x berkata kasar, sekarang dimute 30 detik!"
            await self.mute_member(message.author)
            self.violations[user_id]["bad_words"] = 0
        else:
            warning = f"Kesempatan tersisa: {2 - violation_count}x. Jangan berkata kasar lagi atau kamu akan dimute!"

        embed = discord.Embed(title="⚠️ Bahasa Kasar Terdeteksi", description="Gunakan bahasa yang sopan ya!", color=discord.Color.orange())
        embed.set_thumbnail(url="https://i.imgur.com/9wDAsyz.jpeg")
        embed.add_field(name="Pesan kamu:", value=f"||{message.content[:200]}||", inline=False)
        embed.add_field(name="Kata kasar terdeteksi:", value=", ".join(detected_words), inline=False)
        embed.add_field(name="Peringatan:", value=warning, inline=False)
        embed.set_footer(text="Mari jaga suasana tetap nyaman!")

        try:
            await message.channel.send(message.author.mention, embed=embed, delete_after=15.0)
        except:
            pass

async def setup(bot):
    await bot.add_cog(Spam(bot))
