import subprocess
import sys
import os

def install_requirements():
    # Check if requirements.txt exists
    if os.path.exists("requirements.txt"):
        # Install packages listed in requirements.txt
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        except subprocess.CalledProcessError as e:
            print(f"Error installing requirements: {e}")
            sys.exit(1)
    else:
        print("requirements.txt not found.")
        sys.exit(1)

# Install requirements before running the bot
install_requirements()

import discord
from discord.ext import commands
import wavelink

# Replace 'YOUR_BOT_TOKEN' with your actual bot token
TOKEN = 'MTIxMzA3NDg5MTU4MzEyNzU1Mg.G1TYoU.beYGxSBhguDyj7ayuEnslgyCVrDsAZn9E3vhaQ'

# Set up the bot
intents = discord.Intents.default()
intents.message_content = True  # Required for receiving message content
intents.guilds = True
intents.guild_messages = True
intents.guild_reactions = True
intents.members = True  # Correct attribute for members intent

bot = commands.Bot(command_prefix='!', intents=intents)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'We have logged in as {self.bot.user}')
        # Create a node using wavelink.Client
        async with wavelink.Client(bot=self.bot) as client:
            await client.initiate_node(host='127.0.0.1', port=2333, password='youshallnotpass')

    @commands.command(name='join')
    async def join(self, ctx):
        if not ctx.author.voice:
            await ctx.send("You are not connected to a voice channel")
            return

        channel = ctx.author.voice.channel
        player = ctx.voice_client

        if player is not None:
            if player.channel.id == channel.id:
                return
            try:
                await player.move_to(channel)
            except Exception as e:
                await ctx.send(f"Error: {e}")
        else:
            try:
                await channel.connect(cls=wavelink.Player)
            except Exception as e:
                await ctx.send(f"Error: {e}")

    @commands.command(name='leave')
    async def leave(self, ctx):
        player = ctx.voice_client
        if player is not None:
            await player.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel")

    @commands.command(name='play')
    async def play(self, ctx, *, search: str):
        player = ctx.voice_client

        if not player:
            await ctx.send("The bot is not connected to a voice channel")
            return

        if not player.is_connected():
            await ctx.send("The bot is not connected to a voice channel")
            return

        query = f'ytsearch:{search}'
        tracks = await wavelink.YouTubeTrack.search(query=query)
        if not tracks:
            await ctx.send("No tracks found")
            return

        track = tracks[0]
        await player.play(track)
        await ctx.send(f'Now playing: {track.title}')

    @commands.command(name='pause')
    async def pause(self, ctx):
        player = ctx.voice_client
        if player.is_playing():
            await player.pause()
            await ctx.send("Playback paused")

    @commands.command(name='resume')
    async def resume(self, ctx):
        player = ctx.voice_client
        if player.is_paused():
            await player.resume()
            await ctx.send("Playback resumed")

    @commands.command(name='stop')
    async def stop(self, ctx):
        player = ctx.voice_client
        if player.is_playing():
            await player.stop()
            await ctx.send("Playback stopped")

bot.add_cog(Music(bot))

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason=None):
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')

@bot.command(name='timeout')
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, duration: int, *, reason=None):
    duration_seconds = duration * 60  # Convert minutes to seconds
    await member.timeout(duration=discord.utils.utcnow() + discord.timedelta(seconds=duration_seconds), reason=reason)
    await ctx.send(f'Timeout {member.mention} for {duration} minutes')

@bot.command(name='mute')
@commands.has_permissions(manage_roles=True)
async def mute(ctx, member: discord.Member, *, reason=None):
    mute_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not mute_role:
        mute_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(mute_role, speak=False, send_messages=False, read_message_history=True, read_messages=True)
    await member.add_roles(mute_role, reason=reason)
    await ctx.send(f'Muted {member.mention}')

@bot.command(name='say')
async def say(ctx, *, message):
    await ctx.send(message)

# Custom Help Command
class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Bot Commands", color=discord.Color.blue())
        for cog, commands in mapping.items():
            command_signatures = [self.get_command_signature(c) for c in commands]
            if command_signatures:
                embed.add_field(name=cog.qualified_name if cog else "No Category", value="\n".join(command_signatures), inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command):
        embed = discord.Embed(title=self.get_command_signature(command), description=command.help or "No description", color=discord.Color.blue())
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog):
        embed = discord.Embed(title=cog.qualified_name, description=cog.description, color=discord.Color.blue())
        command_signatures = [self.get_command_signature(c) for c in cog.get_commands()]
        if command_signatures:
            embed.add_field(name="Commands", value="\n".join(command_signatures), inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

bot.help_command = MyHelpCommand()

bot.run(TOKEN)
