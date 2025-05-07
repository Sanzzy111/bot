import discord
from discord.ext import commands
from discord import app_commands
import random, asyncio
import aiosqlite


class TicTacToeButton(discord.ui.Button):
    def __init__(self, x, y):
        super().__init__(label=" ", style=discord.ButtonStyle.secondary, row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view

        if interaction.user != view.current_player:
            return await interaction.response.send_message("Bukan giliran kamu!", ephemeral=True)

        if view.board[self.y][self.x] != 0:
            return await interaction.response.send_message("Kotak ini sudah diisi!", ephemeral=True)

        mark = view.player_marks[view.current_player]
        self.label = mark
        self.style = discord.ButtonStyle.success if mark == "❌" else discord.ButtonStyle.danger
        self.disabled = True
        view.board[self.y][self.x] = mark
        view.last_move = interaction.user
        await interaction.response.edit_message(view=view)

        if view.check_winner(mark):
            for child in view.children:
                child.disabled = True
            await view.cog.record_win(view.current_player.id)
            loser = view.players[0] if view.current_player == view.players[1] else view.players[1]
            await view.cog.record_loss(loser.id)
            return await interaction.followup.send(f"**{mark} ({view.current_player.mention}) menang!**", ephemeral=False)

        if view.is_full():
            for child in view.children:
                child.disabled = True
            return await interaction.followup.send("**Seri!**", ephemeral=False)

        view.switch_turn()
        await interaction.followup.send(f"Giliran {view.current_player.mention} ({view.player_marks[view.current_player]})", ephemeral=False)


class TicTacToeView(discord.ui.View):
    def __init__(self, player1, player2, cog):
        super().__init__(timeout=None)
        self.board = [[0 for _ in range(3)] for _ in range(3)]
        self.players = [player1, player2]
        random.shuffle(self.players)
        self.current_player = self.players[0]
        self.player_marks = {
            self.players[0]: "❌",
            self.players[1]: "⭕"
        }
        self.last_move = self.current_player
        self.message = None
        self.cog = cog

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def switch_turn(self):
        self.current_player = self.players[0] if self.current_player == self.players[1] else self.players[1]

    def check_winner(self, mark):
        for row in self.board:
            if all(cell == mark for cell in row):
                return True
        for col in zip(*self.board):
            if all(cell == mark for cell in col):
                return True
        if all(self.board[i][i] == mark for i in range(3)) or all(self.board[i][2 - i] == mark for i in range(3)):
            return True
        return False

    def is_full(self):
        return all(cell != 0 for row in self.board for cell in row)


class TicTacToeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.ensure_database())

    async def ensure_database(self):
        async with aiosqlite.connect("leaderboard.db") as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS leaderboard (
                    user_id INTEGER PRIMARY KEY,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0
                )
            """)
            await db.commit()

    async def record_win(self, user_id: int):
        async with aiosqlite.connect("leaderboard.db") as db:
            await db.execute("INSERT OR IGNORE INTO leaderboard (user_id, wins, losses) VALUES (?, 0, 0)", (user_id,))
            await db.execute("UPDATE leaderboard SET wins = wins + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    async def record_loss(self, user_id: int):
        async with aiosqlite.connect("leaderboard.db") as db:
            await db.execute("INSERT OR IGNORE INTO leaderboard (user_id, wins, losses) VALUES (?, 0, 0)", (user_id,))
            await db.execute("UPDATE leaderboard SET losses = losses + 1 WHERE user_id = ?", (user_id,))
            await db.commit()

    @app_commands.command(name="tictactoe", description="Tantang seseorang untuk bermain Tic Tac Toe!")
    async def tictactoe(self, interaction: discord.Interaction, user: discord.Member):
        if user == interaction.user:
            return await interaction.response.send_message("Gak bisa main lawan diri sendiri!", ephemeral=True)

        await interaction.response.send_message(
            f"{user.mention}, {interaction.user.mention} ngajak kamu main **Tic Tac Toe**!\nKlik ✅ untuk terima atau ❌ untuk tolak.",
            ephemeral=False
        )
        msg = await interaction.original_response()
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, reactor):
            return (
                reactor.id == user.id
                and str(reaction.emoji) in ["✅", "❌"]
                and reaction.message.id == msg.id
            )

        try:
            reaction, reactor = await self.bot.wait_for("reaction_add", timeout=60.0, check=check)
        except asyncio.TimeoutError:
            return await interaction.followup.send("Waktu habis. Tantangan dibatalkan.")

        if str(reaction.emoji) == "❌":
            return await interaction.followup.send(f"{user.mention} menolak tantangan.")

        view = TicTacToeView(interaction.user, user, self)
        embed = discord.Embed(
            title="Tic Tac Toe",
            description=f"❌ vs ⭕\nGiliran pertama: {view.current_player.mention} ({view.player_marks[view.current_player]})\n\n⏳ **Waktu giliran: 2 menit**",
            color=discord.Color.blurple()
        )
        sent_msg = await interaction.followup.send(embed=embed, view=view)
        view.message = sent_msg

        # Game timeout per giliran
        while True:
            last = view.last_move
            try:
                await asyncio.wait_for(self.bot.wait_for(
                    "interaction",
                    check=lambda i: isinstance(i.message.component, discord.ui.Button) and i.user == view.current_player,
                ), timeout=120)
                break  # tombol ditekan
            except asyncio.TimeoutError:
                # timeout
                for child in view.children:
                    child.disabled = True
                loser = view.current_player
                winner = view.players[0] if view.current_player == view.players[1] else view.players[1]
                await self.record_win(winner.id)
                await self.record_loss(loser.id)
                await view.message.edit(view=view)
                return await interaction.followup.send(
                    f"Waktu habis! {loser.mention} tidak main. {winner.mention} menang otomatis.")

    @app_commands.command(name="leaderboard", description="Lihat top 10 pemain Tic Tac Toe.")
    async def leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect("leaderboard.db") as db:
            cursor = await db.execute("SELECT user_id, wins, losses FROM leaderboard ORDER BY wins DESC LIMIT 10")
            rows = await cursor.fetchall()

        if not rows:
            return await interaction.response.send_message("Belum ada yang main Tic Tac Toe.", ephemeral=True)

        embed = discord.Embed(title="Tic Tac Toe Leaderboard", color=discord.Color.gold())
        for i, (user_id, wins, losses) in enumerate(rows, start=1):
            user = interaction.guild.get_member(user_id) or f"<@{user_id}>"
            embed.add_field(name=f"{i}. {user}", value=f"Menang: **{wins}**, Kalah: **{losses}**", inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    cog = TicTacToeCog(bot)
    bot.tree.add_command(cog.tictactoe)
    bot.tree.add_command(cog.leaderboard)
    await bot.add_cog(cog)
