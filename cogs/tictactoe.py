import discord
from discord.ext import commands
import sqlite3
import random
from dotenv import load_dotenv

load_dotenv()

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label='\u200b', row=y)
        self.x = x
        self.y = y
    
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToeView = self.view
        
        if view.board[self.y][self.x] != 0 or interaction.user != view.current_player:
            return await interaction.response.defer()
        
        view.board[self.y][self.x] = view.current_player_id
        self.style = discord.ButtonStyle.primary if view.current_player_id == 1 else discord.ButtonStyle.danger
        self.label = 'X' if view.current_player_id == 1 else 'O'
        self.disabled = True
        
        winner = view.check_winner()
        if winner is not None:
            if winner == 0:
                content = "It's a tie!"
            else:
                winner_user = view.player1 if winner == 1 else view.player2
                content = f"{winner_user.mention} wins!"
                await update_leaderboard(winner_user.id)
            
            for child in view.children:
                child.disabled = True
            
            view.stop()
            await interaction.response.edit_message(content=content, view=view)
        else:
            view.current_player = view.player2 if view.current_player_id == 1 else view.player1
            view.current_player_id = 3 - view.current_player_id
            await interaction.response.edit_message(content=f"It's {view.current_player.mention}'s turn!", view=view)

class TicTacToeView(discord.ui.View):
    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__(timeout=180)
        self.player1 = player1
        self.player2 = player2
        
        # Randomize who starts first
        if random.choice([True, False]):
            self.current_player = player1
            self.current_player_id = 1
        else:
            self.current_player = player2
            self.current_player_id = 2
            
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0]
        ]
        
        for x in range(3):
            for y in range(3):
                self.add_item(TicTacToeButton(x, y))
    
    def check_winner(self):
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.board[0][col]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]
        
        # Check for tie
        if all(all(cell != 0 for cell in row) for row in self.board):
            return 0
        
        return None

async def update_leaderboard(user_id: int):
    conn = sqlite3.connect('tictactoe.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS leaderboard
                 (user_id INTEGER PRIMARY KEY, wins INTEGER DEFAULT 0)''')
    
    c.execute('INSERT OR IGNORE INTO leaderboard (user_id, wins) VALUES (?, 0)', (user_id,))
    c.execute('UPDATE leaderboard SET wins = wins + 1 WHERE user_id = ?', (user_id,))
    
    conn.commit()
    conn.close()

class InviteView(discord.ui.View):
    def __init__(self, inviter: discord.Member, invitee: discord.Member):
        super().__init__(timeout=60)
        self.inviter = inviter
        self.invitee = invitee
        self.accepted = False
    
    @discord.ui.button(emoji='✅', style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.invitee:
            return await interaction.response.send_message("Hanya yang diundang yang bisa menerima!", ephemeral=True)
        
        self.accepted = True
        self.stop()
        
        # Start the game
        view = TicTacToeView(self.inviter, self.invitee)
        await interaction.response.edit_message(
            content=f"Permainan dimulai!\n{view.player1.mention} (X) vs {view.player2.mention} (O)\nSekarang giliran {view.current_player.mention}!",
            view=view
        )
    
    @discord.ui.button(emoji='❌', style=discord.ButtonStyle.red)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.invitee:
            return await interaction.response.send_message("Hanya yang diundang yang bisa menolak!", ephemeral=True)
        
        self.stop()
        await interaction.response.edit_message(content=f"{self.invitee.mention} menolak permainan Tic Tac Toe.", view=None)
    
    async def on_timeout(self):
        if not self.accepted:
            try:
                message = self.message
                await message.edit(content=f"Undangan Tic Tac Toe dari {self.inviter.mention} telah kadaluarsa.", view=None)
            except:
                pass

class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.initialize_db()
    
    def initialize_db(self):
        conn = sqlite3.connect('tictactoe.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS leaderboard
                     (user_id INTEGER PRIMARY KEY, wins INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Cog {self.__class__.__name__} is ready.')
    
    @discord.app_commands.command(name="tictactoe", description="Mainkan Tic Tac Toe dengan temanmu")
    async def tictactoe_slash(self, interaction: discord.Interaction, opponent: discord.Member):
        """Slash command untuk memulai permainan Tic Tac Toe"""
        if opponent == interaction.user:
            return await interaction.response.send_message("Kamu tidak bisa bermain melawan dirimu sendiri!", ephemeral=True)
        if opponent.bot:
            return await interaction.response.send_message("Kamu tidak bisa bermain melawan bot!", ephemeral=True)
        
        view = InviteView(interaction.user, opponent)
        await interaction.response.send_message(
            f"{interaction.user.mention} mengajak {opponent.mention} bermain Tic Tac Toe!\n"
            f"{opponent.mention}, klik ✅ untuk menerima atau ❌ untuk menolak.",
            view=view
        )
        view.message = await interaction.original_response()
    
    @discord.app_commands.command(name="tictactoe_leaderboard", description="Lihat leaderboard Tic Tac Toe")
    async def leaderboard_slash(self, interaction: discord.Interaction, top: int = 10):
        """Slash command untuk menampilkan leaderboard"""
        if top < 1 or top > 25:
            return await interaction.response.send_message("Silakan masukkan angka antara 1-25 untuk jumlah pemain.", ephemeral=True)
        
        conn = sqlite3.connect('tictactoe.db')
        c = conn.cursor()
        
        c.execute('SELECT user_id, wins FROM leaderboard ORDER BY wins DESC LIMIT ?', (top,))
        records = c.fetchall()
        conn.close()
        
        if not records:
            return await interaction.response.send_message("Belum ada permainan yang dimainkan!", ephemeral=True)
        
        leaderboard_text = "🏆 Tic Tac Toe Leaderboard 🏆\n\n"
        for idx, (user_id, wins) in enumerate(records, 1):
            user = self.bot.get_user(user_id)
            username = user.mention if user else f"Unknown User ({user_id})"
            leaderboard_text += f"{idx}. {username}: {wins} {'win' if wins == 1 else 'wins'}\n"
        
        embed = discord.Embed(
            title="Tic Tac Toe Leaderboard",
            description=leaderboard_text,
            color=discord.Color.gold()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(TicTacToe(bot))