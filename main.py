import discord
from discord.ext import commands
import os
from keep_alive import keep_alive
from commands import get_prefix, Commands
import asyncio
from timeit import default_timer as t
from Database import DB

print(os.getcwd())
token = os.environ['TOKEN']

intents = discord.Intents().all()
client = commands.Bot(intents=intents, command_prefix=lambda client, message: get_prefix(message.guild.id))
db = DB("db/Servers", cached=True, cached_children=True)

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await client.load_extension(f"cogs.{filename[:-3]}")
            
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await load_extensions()
    
cluster = Commands(client=client, group="Sero", description="Group of commands limited to the owner")

@cluster.static_command(mention_as_prefix=True)
async def load(ctx, extension):
    """Loads cog"""
    if ctx.author.id == 396860451713187843:
        await client.load_extension(f"cogs.{extension}")
        await ctx.reply(f"Loading extension {extension}...", mention_author=False)

@cluster.static_command(mention_as_prefix=True)
async def unload(ctx, extension):
    """Unloads cog"""
    if ctx.author.id == 396860451713187843:
        await client.unload_extension(f"cogs.{extension}")
        await ctx.reply(f"Unloading extension {extension}...", mention_author=False)

@cluster.static_command(mention_as_prefix=True)
async def reload(ctx, extension):
    """Reloads cog"""
    if ctx.author.id == 396860451713187843:
        await client.unload_extension(f"cogs.{extension}")
        await client.load_extension(f"cogs.{extension}")
        await ctx.reply(f"Reloading extension {extension}...", mention_author=False)

@cluster.static_command(mention_as_prefix=True)
async def abort(ctx, args):
    """Kills the program"""
    if ctx.author.id == 396860451713187843:
        await ctx.channel.send("Aborting... Confirm?")
        confirm = ["y", "yes", "confirm"]
        back = ["n", "no"]
        try:
            def check(m):
                m.channel=ctx.channel and m.content in confirm.extend(back)
            message = await client.wait_for("message", timeout=60, check=check)
            if message.content in confirm:
                await message.reply("Shutting down...", mention_author=False)
                os._exit(0)
            else:
                await message.reply("Stayin alive", mention_author=False)
        except asyncio.TimeoutError:
            await message.reply("Stayin alive", mention_author=False)
            
@cluster.static_command(mention_as_prefix=True, ignore_case=True)
async def ping(context, content):
    await context.send(f"Pong! The latency is `{round(client.latency * 1000)}ms` ({round(client.latency, 6)}s)")

@cluster.static_command(mention_as_prefix=True, ignore_case=True)
async def groups(context, content):
    print(cluster.groups)

@cluster.static_command(ignore_case=True)
async def database(ctx, content):
    print(db._control)
    for server in db.data.values():
        print(server._control)

@client.event
async def on_message(message):
    cluster.process_commands(message)


keep_alive()
try:
    client.run(token)
except:
    os.system("kill 1")