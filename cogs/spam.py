import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
import json
import os

class Spam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # Anti-spam settings
        self.spam_control = commands.CooldownMapping.from_cooldown(
            5, 15.0, commands.BucketType.user
        )
        
        # Bad word filter (customize this list as needed)
        self.bad_words = [
            "anjing", "bangsat", "kontol", "memek", 
            "jancok", "asu", "bajingan", "ngentot"
        ]
        
        # Violation tracking
        self.violations = {}  # Format: {user_id: {"spam": count, "bad_words": count}}
        
        # Load violations from file if exists
        if os.path.exists('data/violations.json'):
            with open('data/violations.json', 'r') as f:
                self.violations = json.load(f)
        else:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
    
    def save_violations(self):
        with open('data/violations.json', 'w') as f:
            json.dump(self.violations, f)
    
    async def mute_member(self, member, duration=30):
        muted_role = discord.utils.get(member.guild.roles, name="Muted")
        
        # Create muted role if it doesn't exist
        if not muted_role:
            muted_role = await member.guild.create_role(name="Muted")
            
            # Apply permission overwrites to all channels
            for channel in member.guild.channels:
                await channel.set_permissions(muted_role,
                    send_messages=False,
                    add_reactions=False,
                    speak=False)
        
        await member.add_roles(muted_role)
        
        # Unmute after duration
        await asyncio.sleep(duration)
        await member.remove_roles(muted_role)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
            
        try:
            # Initialize user in violations tracker if not exists
            if str(message.author.id) not in self.violations:
                self.violations[str(message.author.id)] = {
                    "spam": 0,
                    "bad_words": 0
                }
            
            user_violations = self.violations[str(message.author.id)]
            action_taken = False
            
            # Anti-spam check
            bucket = self.spam_control.get_bucket(message)
            retry_after = bucket.update_rate_limit()
            
            if retry_after:
                user_violations["spam"] += 1
                action_taken = True
                await self.handle_spam(message, user_violations["spam"])
                
            # Bad word check
            content_lower = message.content.lower()
            detected_words = [word for word in self.bad_words if word in content_lower]
            
            if detected_words:
                user_violations["bad_words"] += 1
                action_taken = True
                await self.handle_bad_words(message, detected_words, user_violations["bad_words"])
            
            if action_taken:
                self.save_violations()
        except Exception as e:
            print(f"Error in moderation: {e}")

    async def handle_spam(self, message, violation_count):
        try:
            await message.delete()
        except:
            pass
        
        remaining_chances = 3 - violation_count
        mute_warning = ""
        
        if violation_count >= 3:
            # Mute the user for 30 seconds
            mute_warning = "Karena ini pelanggaran ke-3, kamu aku mute 30 detik! 😠"
            await self.mute_member(message.author)
            self.violations[str(message.author.id)]["spam"] = 0  # Reset counter
        else:
            mute_warning = f"Kesempatan tersisa: {remaining_chances}x. Kalau spam lagi, aku mute 30 detik ya! 😤"
        
        embed = discord.Embed(
            title="Waduh, Santai Bro! 🚨",
            description="Jangan spam dong, nanti aku pusing 😵",
            color=discord.Color.red()
        )
        embed.set_thumbnail(url="https://i.imgur.com/9wDAsyz.jpeg")
        embed.add_field(
            name="Warning:",
            value=mute_warning,
            inline=False
        )
        embed.add_field(
            name="Tips:",
            value="Coba jeda dikit ya, biar obrolan lebih enak dibaca 😊",
            inline=False
        )
        embed.set_footer(text="Aturan server: No spam!")
        
        try:
            await message.channel.send(
                f"{message.author.mention}",
                embed=embed,
                delete_after=15.0
            )
        except:
            pass
    
    async def handle_bad_words(self, message, detected_words, violation_count):
        try:
            await message.delete()
        except:
            pass
        
        remaining_chances = 3 - violation_count
        mute_warning = ""
        
        if violation_count >= 3:
            # Mute the user for 30 seconds
            mute_warning = "Ini udah 3x ngomong kasar, kamu aku mute 30 detik! 🤬"
            await self.mute_member(message.author)
            self.violations[str(message.author.id)]["bad_words"] = 0  # Reset counter
        else:
            mute_warning = f"Kesempatan tersisa: {remaining_chances}x. Kalau kasar lagi, aku mute ya! 😠"
        
        embed = discord.Embed(
            title="Woi, Jangan Kasar! ⚠️",
            description="Bahasa yang baik itu keren lho 😎",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url="https://i.imgur.com/9wDAsyz.jpeg")
        embed.add_field(
            name="Pesan kamu:",
            value=f"||{message.content[:200]}||",
            inline=False
        )
        embed.add_field(
            name="Kata yang terdeteksi:",
            value=", ".join(detected_words),
            inline=False
        )
        embed.add_field(
            name="Warning:",
            value=mute_warning,
            inline=False
        )
        embed.set_footer(text="Mari jaga kerukunan!")
        
        try:
            await message.channel.send(
                f"{message.author.mention}",
                embed=embed,
                delete_after=15.0
            )
        except:
            pass

async def setup(bot):
    await bot.add_cog(Spam(bot))