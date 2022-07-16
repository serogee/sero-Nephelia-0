import discord
import re
from Database import DB
import asyncio
from timeit import default_timer as t

default_prefix = "&"
color = 0x0e8bf3
bot_name = "Nephelia"
bot_emoji = "💠"
mudae = 432610292342587392

def default_embed(client, prefix, name):
    embed = discord.Embed(
        title=f"═════════\nHelp: **{name}**\n\u200b",
        color=color
        )
    embed.set_author(name=bot_name, icon_url=client.user.avatar)
    embed.set_thumbnail(url=client.user.avatar)
    embed.set_footer(text=f"{bot_emoji} {prefix}{name} {bot_emoji}")
    return embed

db = DB("db/Servers", cached=True, cached_children=True)

def has_perms(author, gid):
    if author.guild_permissions.administrator:
        return True
    else:
        try:
            author_roles = [ar.id for ar in author.roles]
            for role in db[f"{gid}"]["Admins"]:
                if role in author_roles:
                    return True
            return False
        except KeyError:
            return False
            
def get_prefix(gid):
    key = str(gid)
    try:
        if key in db: 
            return db[key]["Prefix"]
        else: 
            return default_prefix
    except:
        return default_prefix


class Flags:

    def __init__(self, flags):
        self.text = flags

    def __str__(self):
        if self.text:
            return self.text
        return ""

    def __contains__(self, flag: str):
        try:
            return flag in self.text
        except TypeError:
            return None        

    def has_flag(self, flag):
        try:
            return flag in self.text
        except TypeError:
            return None

    def input(self, input):
        try:
            return re.search(input, self.text)
        except TypeError:
            return None

        
class Context:

    def __init__(self, message, prefix, trigger, flags, command):
        self.command = command
        self.trigger = trigger
        self.prefix = prefix
        self.message = message
        self.guild = message.guild
        self.channel = message.channel
        self.send = message.channel.send
        self.delete = message.delete
        self.author = message.author
        self.flags = Flags(flags)

    async def reply(self, content=None, embed=None, mention_author=False):
        await self.message.reply(content, embed=embed, mention_author=mention_author)

    async def get_reference(self):
        try:
            return await self.channel.fetch_message(self.message.reference.message_id)
        except:
            return None
        
    
class Command:

    def __init__(self, traceback, group, *, flagged: bool=True, aliases: list=[], flag_modes: dict={}, mention_as_prefix=False, ignore_case=False):
        self.traceback = traceback
        self.aliases = aliases
        self.flag_modes = flag_modes
        self.name = traceback.__name__
        self.description = traceback.__doc__
        self.mention_as_prefix = mention_as_prefix
        self.ignore_case = ignore_case
        self.triggers = [self.name] + aliases
        self.group = group
        self.flagged = flagged
        self.client = self.group.client
        regex = []
        def anycase(mat):
            group1 = mat.group(1)
            return f"[{group1.lower()}{group1.upper()}]"
        for trigger in self.triggers:
            trigger = re.sub(r"([\W])", r"\\\1", trigger)
            if ignore_case: trigger = re.sub(r"([a-zA-Z])", anycase, trigger)
            regex.append(trigger)
        self.triggers_re = fr"{'|'.join(regex)}"

    def embed(self, prefix):
        """Returns the help information of a command as a discord.Embed"""
        embed = discord.Embed(
            title=f"═════════\nHelp: **{self.name}**\n\u200b",
            color=color
            )
        embed.set_author(name=bot_name, icon_url=self.client.user.avatar)
        embed.set_thumbnail(url=self.client.user.avatar)
        embed.set_footer(text=f"{bot_emoji} {prefix}{self.name} {bot_emoji}")
        embed.description = f"```\n - {self.description}\n```\u200b"
        if self.aliases:
            embed.add_field(name=f"__Aliases__", value=", ".join([f"`{prefix}{alias}`" for alias in self.aliases]) + "\n\u200b", inline=False)
        for mode, flags in self.flag_modes.items():
            embed.add_field(name=f"__{mode}__", value="\n".join([f"> **{flag}**\n```\n  {desc}\n```" for flag, desc in flags.items()]) + "\u200b", inline=False)
        return embed
        
    def __iter__(self):
        yield self.name
        for alias in self.aliases:
            yield alias

    def __contains__(self, item):
        return item in self.triggers

    def invoked(self, item):
        """Returns True if item starts with the command name or any of its alias"""
        if self.ignore_case:
            item = item.lower()
        for trigger in self:
            if item.startswith(trigger): return True
        return False


class Commands(object):

    groups = dict()
    client = None

    def __new__(cls, client=None, group="Default", description="No description set."):
        if group in cls.groups:
            return cls.groups[group]
        return super(Commands, cls).__new__(cls)

    def __init__(self, client=None, group="Default", description="No description set."):
        self.groups[group] = self
        if not self.client:
            Commands.client = client
        
        self.commands = []
        self.name = group
        self.description = description
        self._command_re = []

    def __contains__(self, item):
        for command in self.commands:
            if item in command: return True
        return False

    def __iter__(self):
        return iter(self.commands)

    def invoked(self, item):
        for command in self.commands:
            if command.invoked(item): return True
        return False

    def flagged_command(self, *args, **kwargs):
        def deco(func):
            command = Command(
                traceback=func, 
                group=self, 
                *args,
                **kwargs
            )
            self.commands.append(command)
            self._command_re.append((command, command.triggers_re))
            return func
        return deco

    def static_command(self, *args, **kwargs):
        def deco(func):
            command = Command(
                traceback=func, 
                group=self, 
                flagged=False,
                *args,
                **kwargs
            )
            self.commands.append(command)
            self._command_re.append((command, command.triggers_re))
            return func
        return deco
    

    def process_commands(self, message):
        content = message.content
        mgid = message.guild.id
        p = get_prefix(mgid)

        prefix = content.startswith(p)
        if prefix:
            content = content.replace(p, "", 1)
        else:
            mention = f"<@{self.client.user.id}>"
            if content.startswith(mention):
                content = content.replace(mention, "", 1)
            else: return
        

        for command, regex in self._command_re:
            if not prefix:
                if not command.mention_as_prefix:
                    return 
            if command.flagged: 
                match = re.search(rf"^[ \n]*({regex})([^ \t\n\u200b]+)?(?:[ \t\n\u200b]+(.+)?)?$", content, re.DOTALL)
                if match:
                    asyncio.ensure_future(command.traceback(
                        Context(message, p, match.group(1), match.group(2), command), 
                        match.group(3)
                    ))
            else:
                match = re.search(rf"^[ \n]*({regex})(?:[ \t\n\u200b]+(.+)?)?$", content, re.DOTALL)
                if match:
                    asyncio.ensure_future(command.traceback(
                        Context(message, p, match.group(1), None, command), 
                        match.group(2)
                    ))

    @classmethod
    def process_all(cls, message):
        for group in cls.groups.values():
            group.process_commands(message)

    @classmethod
    def search_group(cls, item):
        for name, group in cls.groups.items():
            if name.lower() == item.lower():
                return group
        return None

    @classmethod
    def search_command(cls, item):
        for group in cls.groups.values():
            for command in group:
                for trigger in command:
                    if trigger.lower() == item.lower():
                        return command
        return None