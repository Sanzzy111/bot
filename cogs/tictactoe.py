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
        self.current_player = random.choice([player1, player2])  # Pemain pertama random
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

class ConfirmView(View):
    def __init__(self, inviter, opponent):
        super().__init__(timeout=60)
        self.inviter = inviter
        self.opponent = opponent
        self.confirmed = False
    
    @discord.ui.button(emoji="✅", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("Hanya yang diundang yang bisa menerima!", ephemeral=True)
            return
            
        self.confirmed = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(emoji="❌", style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.opponent:
            await interaction.response.send_message("Hanya yang diundang yang bisa menolak!", ephemeral=True)
            return
            
        self.stop()
        await interaction.response.defer()

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="tictactoe",
        description="Undang temanmu main Tic Tac Toe"
    )
    @app_commands.describe(lawan="Pilih lawan mainmu")
    async def tic_tac_toe(self, interaction: discord.Interaction, lawan: discord.Member):
        """Memulai permainan Tic Tac Toe dengan konfirmasi reaction"""
        
        if lawan.bot:
            return await interaction.response.send_message("Bots tidak bisa main Tic Tac Toe!", ephemeral=True)
            
        if lawan == interaction.user:
            return await interaction.response.send_message("Tidak bisa main sendiri!", ephemeral=True)
        
        # Kirim pesan undangan dengan button
        embed = discord.Embed(
            title="🎮 Undangan Tic Tac Toe",
            description=(
                f"{lawan.mention}, kamu diundang main Tic Tac Toe oleh {interaction.user.mention}!\n\n"
                "Klik tombol dibawah untuk:\n"
                "✅ Terima undangan\n"
                "❌ Tolak undangan\n\n"
                "Undangan akan kadaluarsa dalam 1 menit."
            ),
            color=discord.Color.blue()
        )
        
        view = ConfirmView(interaction.user, lawan)
        await interaction.response.send_message(embed=embed, view=view)
        await view.wait()
        
        if view.is_finished():
            if view.confirmed:
                # Mulai game
                game_view = TicTacToeView(interaction.user, lawan)
                
                embed = discord.Embed(
                    title="🎮 Tic Tac Toe",
                    description=(
                        f"**Pemain 1:** ❌ {interaction.user.mention}\n"
                        f"**Pemain 2:** ⭕ {lawan.mention}\n\n"
                        f"🔹 Giliran: {game_view.current_player.mention}\n\n"
                        f"{game_view.get_board_str()}"
                    ),
                    color=discord.Color.green()
                )
                
                message = await interaction.original_response()
                await message.edit(embed=embed, view=game_view)
            else:
                embed = discord.Embed(
                    description=f"❌ {lawan.mention} menolak undangan main.",
                    color=discord.Color.red()
                )
                await interaction.edit_original_response(embed=embed, view=None)
        else:
            embed = discord.Embed(
                description="⏰ Waktu konfirmasi habis, undangan dibatalkan.",
                color=discord.Color.light_grey()
            )
            await interaction.edit_original_response(embed=embed, view=None)

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))