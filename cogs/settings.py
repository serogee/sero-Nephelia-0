from commands import Commands, has_perms, default_prefix
from discord.ext import commands
from Database import DB
import re

db = DB("db/Servers", cached=True, cached_children=True)

cluster = Commands(group="Settings", description="Commands for editing server preferences.")

class Settings(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_message(self, message):
        cluster.process_commands(message)


@cluster.static_command(mention_as_prefix=True, ignore_case=True)
async def prefix(ctx, content):
    """Changes my prefix for this server."""
    gid = ctx.guild.id
    if not content:
        p = ctx.prefix
        if cluster.client.user.mentioned_in(ctx.message):
            await ctx.send(f"My current prefix for this server is `{p}`")
        else:
            await ctx.send(embed=ctx.command.embed(p))
    elif has_perms(ctx.author, gid):
        if content == default_prefix:
            try:
                del db[str(gid)]["Prefix"]
            except KeyError:
                pass
            await ctx.send(f"My prefix for this server has been set to the default, `{content}`.")
        else:
            try:
                db[str(gid)]["Prefix"] = content
            except KeyError:
                db[str(gid)] = {"Prefix": content}
            await ctx.send(f"My prefix for this server has been set to `{content}`")
    else:
        await ctx.send("You do not have permission to change my prefix!")

@cluster.flagged_command(aliases=["admin", "mods", "mod"])
async def admins(ctx, content):
    if content:
        ids = re.findall(r"\d{18}", content)
        if ids:
            roles = []
            for id in ids:
                try:
                    role = ctx.guild.get_role(id)
                    roles.append((role, id))
                except:
                    pass
            if ctx.flags.has_flag("r"):
                
                    

  
async def setup(client):
    await client.add_cog(Settings(client))