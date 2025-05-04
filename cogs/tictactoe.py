import discord
from discord.ext import commands
from discord.ui import Button, View
import random
from discord import app_commands
import asyncio

class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y
    
    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user not in (view.player1, view.player2):
            await interaction.response.send_message("Kamu bukan peserta game ini!", ephemeral=True)
            return
        if interaction.user != view.current_player:
            await interaction.response.send_message("Tunggu giliranmu ya!", ephemeral=True)
            return
            
        if view.board[self.y][self.x] == 0:
            view.board[self.y][self.x] = 1 if view.current_player == view.player1 else 2
            self.style = discord.ButtonStyle.red if view.current_player == view.player1 else discord.ButtonStyle.blurple
            self.label = '❌' if view.current_player == view.player1 else '⭕'
            self.disabled = True
            
            winner = view.check_winner()
            if winner:
                for child in view.children:
                    child.disabled = True
                view.stop()
                
                if winner == "draw":
                    embed = discord.Embed(
                        title="🎮 Tic Tac Toe - SERI!",
                        description=f"Permainan berakhir seri!\n{view.get_board_str()}",
                        color=discord.Color.orange()
                    )
                else:
                    embed = discord.Embed(
                        title="🎮 Tic Tac Toe - MENANG!",
                        description=f"🎉 {winner.mention} menang!\n{view.get_board_str()}",
                        color=discord.Color.green()
                    )
                
                await interaction.response.edit_message(embed=embed, view=view)
                return
            
            view.current_player = view.player2 if view.current_player == view.player1 else view.player1
            
            embed = interaction.message.embeds[0]
            embed.description = (
                f"**Pemain 1:** ❌ {view.player1.mention}\n"
                f"**Pemain 2:** ⭕ {view.player2.mention}\n\n"
                f"🔹 Giliran: {view.current_player.mention}\n\n"
                f"{view.get_board_str()}"
            )
            
            await interaction.response.edit_message(embed=embed, view=view)

class TicTacToeView(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=300)
        self.player1 = player1
        self.player2 = player2
        self.current_player = random.choice([player1, player2])
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))
    
    def get_board_str(self):
        board_str = ""
        for y in range(3):
            for x in range(3):
                if self.board[y][x] == 0:
                    board_str += "⬜"
                elif self.board[y][x] == 1:
                    board_str += "❌"
                else:
                    board_str += "⭕"
            board_str += "\n"
        return board_str
    
    def check_winner(self):
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return self.player1 if row[0] == 1 else self.player2
        
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.player1 if self.board[0][col] == 1 else self.player2
        
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.player1 if self.board[0][0] == 1 else self.player2
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.player1 if self.board[0][2] == 1 else self.player2
        
        if all(cell != 0 for row in self.board for cell in row):
            return "draw"
        
        return None

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_invites = {}
    
    @app_commands.command(
        name="tictactoe",
        description="Undang temanmu main Tic Tac Toe"
    )
    @app_commands.describe(lawan="Pilih lawan mainmu")
    async def tic_tac_toe(self, interaction: discord.Interaction, lawan: discord.Member):
        """Memulai permainan Tic Tac Toe dengan konfirmasi"""
        
        if lawan.bot:
            return await interaction.response.send_message("Bots tidak bisa main Tic Tac Toe!", ephemeral=True)
            
        if lawan == interaction.user:
            return await interaction.response.send_message("Tidak bisa main sendiri!", ephemeral=True)
        
        # Kirim pesan undangan
        embed = discord.Embed(
            title="🎮 Undangan Tic Tac Toe",
            description=(
                f"{lawan.mention}, kamu diundang main Tic Tac Toe oleh {interaction.user.mention}!\n\n"
                "Balas pesan ini dengan:\n"
                "✅ `YA` untuk menerima\n"
                "❌ `TIDAK` untuk menolak\n\n"
                "Undangan akan kadaluarsa dalam 1 menit."
            ),
            color=discord.Color.blue()
        )
        
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        
        # Simpan data undangan
        self.pending_invites[msg.id] = {
            "inviter": interaction.user,
            "opponent": lawan,
            "message": msg
        }
        
        # Set timeout 1 menit
        await asyncio.sleep(60)
        if msg.id in self.pending_invites:
            del self.pending_invites[msg.id]
            await msg.delete()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        # Cek apakah pesan adalah balasan untuk undangan
        if not message.reference:
            return
            
        if message.reference.message_id not in self.pending_invites:
            return
            
        invite = self.pending_invites[message.reference.message_id]
        
        # Cek apakah pengirim adalah lawan yang diundang
        if message.author != invite["opponent"]:
            return
        
        # Proses jawaban
        content = message.content.lower()
        if content in ("ya", "yes", "y", "ok", "gas"):
            # Mulai game
            view = TicTacToeView(invite["inviter"], invite["opponent"])
            
            embed = discord.Embed(
                title="🎮 Tic Tac Toe",
                description=(
                    f"**Pemain 1:** ❌ {invite['inviter'].mention}\n"
                    f"**Pemain 2:** ⭕ {invite['opponent'].mention}\n\n"
                    f"🔹 Giliran: {view.current_player.mention}\n\n"
                    f"{view.get_board_str()}"
                ),
                color=discord.Color.green()
            )
            
            await invite["message"].edit(embed=embed, view=view)
            del self.pending_invites[message.reference.message_id]
            
        elif content in ("tidak", "no", "n", "tolak"):
            embed = discord.Embed(
                description=f"❌ {invite['opponent'].mention} menolak undangan main.",
                color=discord.Color.red()
            )
            await invite["message"].edit(embed=embed)
            del self.pending_invites[message.reference.message_id]
        
        try:
            await message.delete()
        except:
            pass

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))