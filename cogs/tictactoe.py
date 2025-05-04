import discord
from discord.ext import commands
from discord.ui import Button, View
import random
from discord import app_commands
import asyncio

class TicTacToeGame:
    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2
        self.current_player = random.choice([player1, player2])
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
    
    def make_move(self, x, y):
        if self.board[y][x] != 0:
            return False
        
        self.board[y][x] = 1 if self.current_player == self.player1 else 2
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        return True
    
    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return self.player1 if row[0] == 1 else self.player2
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.player1 if self.board[0][col] == 1 else self.player2
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.player1 if self.board[0][0] == 1 else self.player2
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.player1 if self.board[0][2] == 1 else self.player2
        
        # Check draw
        if all(cell != 0 for row in self.board for cell in row):
            return "draw"
        
        return None
    
    def get_board_str(self):
        symbols = ["⬜", "❌", "⭕"]
        return "\n".join("".join(symbols[cell] for cell in row) for row in self.board)

class TicTacToeButton(Button):
    def __init__(self, x, y):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y
    
    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        
        # Verify player
        if interaction.user not in (view.game.player1, view.game.player2):
            await interaction.response.send_message("Kamu bukan peserta game ini!", ephemeral=True)
            return
        
        if interaction.user != view.game.current_player:
            await interaction.response.send_message("Tunggu giliranmu ya!", ephemeral=True)
            return
        
        # Process move
        if view.game.make_move(self.x, self.y):
            self.label = "❌" if interaction.user == view.game.player1 else "⭕"
            self.style = discord.ButtonStyle.red if interaction.user == view.game.player1 else discord.ButtonStyle.blurple
            self.disabled = True
            
            # Check game status
            winner = view.game.check_winner()
            if winner:
                for child in view.children:
                    child.disabled = True
                view.stop()
                
                if winner == "draw":
                    embed = discord.Embed(
                        title="🎮 Tic Tac Toe - SERI!",
                        description=f"Permainan berakhir seri!\n\n{view.game.get_board_str()}",
                        color=discord.Color.orange()
                    )
                else:
                    embed = discord.Embed(
                        title="🎮 Tic Tac Toe - MENANG!",
                        description=f"🎉 {winner.mention} menang!\n\n{view.game.get_board_str()}",
                        color=discord.Color.green()
                    )
                
                await interaction.response.edit_message(embed=embed, view=view)
            else:
                embed = discord.Embed(
                    title="🎮 Tic Tac Toe",
                    description=(
                        f"**Pemain 1:** ❌ {view.game.player1.mention}\n"
                        f"**Pemain 2:** ⭕ {view.game.player2.mention}\n\n"
                        f"🔹 Giliran: {view.game.current_player.mention}\n\n"
                        f"{view.game.get_board_str()}"
                    ),
                    color=discord.Color.blue()
                )
                await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("Kotak ini sudah terisi!", ephemeral=True)

class TicTacToeView(View):
    def __init__(self, game):
        super().__init__(timeout=300)
        self.game = game
        
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

class ConfirmView(View):
    def __init__(self, inviter, opponent):
        super().__init__(timeout=60)
        self.inviter = inviter
        self.opponent = opponent
    
    @discord.ui.button(label="Terima", style=discord.ButtonStyle.green, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("Hanya yang diundang yang bisa menerima!", ephemeral=True)
            return
        
        game = TicTacToeGame(self.inviter, self.opponent)
        view = TicTacToeView(game)
        
        embed = discord.Embed(
            title="🎮 Tic Tac Toe",
            description=(
                f"**Pemain 1:** ❌ {game.player1.mention}\n"
                f"**Pemain 2:** ⭕ {game.player2.mention}\n\n"
                f"🔹 Giliran: {game.current_player.mention}\n\n"
                f"{game.get_board_str()}"
            ),
            color=discord.Color.green()
        )
        
        await interaction.response.edit_message(embed=embed, view=view)
        self.stop()
    
    @discord.ui.button(label="Tolak", style=discord.ButtonStyle.red, emoji="❌")
    async def reject(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("Hanya yang diundang yang bisa menolak!", ephemeral=True)
            return
        
        embed = discord.Embed(
            description=f"❌ {self.opponent.mention} menolak undangan main.",
            color=discord.Color.red()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_games = {}
    
    async def setup_hook(self):
        # Register slash command
        self.bot.tree.add_command(self.tic_tac_toe)
        await self.bot.tree.sync()
        print("Tic Tac Toe command registered!")
    
    @app_commands.command(
        name="tictactoe",
        description="Mulai permainan Tic Tac Toe dengan teman"
    )
    @app_commands.describe(opponent="Pilih lawan mainmu")
    @app_commands.default_permissions(use_application_commands=True)
    async def tic_tac_toe(self, interaction: discord.Interaction, opponent: discord.Member):
        """Memulai permainan Tic Tac Toe dengan konfirmasi"""
        if opponent.bot:
            return await interaction.response.send_message("Bots tidak bisa main Tic Tac Toe!", ephemeral=True)
        
        if opponent == interaction.user:
            return await interaction.response.send_message("Tidak bisa main sendiri!", ephemeral=True)
        
        # Kirim pesan undangan
        embed = discord.Embed(
            title="🎮 Undangan Tic Tac Toe",
            description=(
                f"{opponent.mention}, kamu diundang main oleh {interaction.user.mention}!\n\n"
                "Klik tombol dibawah untuk:\n"
                "✅ Terima undangan\n"
                "❌ Tolak undangan\n\n"
                "Undangan kadaluarsa dalam 1 menit."
            ),
            color=discord.Color.blue()
        )
        
        view = ConfirmView(interaction.user, opponent)
        await interaction.response.send_message(embed=embed, view=view)
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Tic Tac Toe cog ready! Logged in as {self.bot.user}")

async def setup(bot):
    cog = TicTacToe(bot)
    await bot.add_cog(cog)
    # Sync commands saat cog dimuat
    await bot.tree.sync()
    print("Tic Tac Toe commands synced!")