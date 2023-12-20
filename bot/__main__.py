"""Bot entry point."""

import asyncio
import os
import platform
import random
from datetime import datetime

import discord
from aiohttp import ClientSession
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from lib.consts import C_ERROR, PREFIX, TOKEN

intents = discord.Intents.default()

intents.members = True
intents.message_content = True
intents.presences = True


class Primed(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time: datetime = datetime.utcnow()

    async def close(self) -> None:
        """Close the aiohttp session when the bot is closed."""
        await super().close()
        await self.session.close()

    async def setup_hook(self) -> None:
        """Load cogs and start the bot."""
        self.session: ClientSession = ClientSession(loop=self.loop)
        await self.load_cogs()
        await self.tree.sync()

    async def load_cogs(self) -> None:  # noqa: D103
        for file in os.listdir("./bot/exts"):
            if file.endswith(".py"):
                ext = file[:-3]
                try:
                    await self.load_extension(f"exts.{ext}")
                    print(f"'{ext}' loaded")
                except Exception as e:
                    exception = f"{type(e).__name__}: {e}"
                    print(f"Exception on loading {ext}\n{exception}")

    async def on_ready(self) -> None:
        """Start the status task when the bot is ready."""
        print("loaded aiohttp session")
        print("-------------------")
        print(f"{self.user.name}#{self.user.discriminator}")  # type: ignore
        print(f"discord.py {discord.__version__}")
        print(f"Python {platform.python_version()}")
        print(f"{platform.system()} {platform.release()} ({os.name})")
        print("-------------------")

    async def on_message(self, message: discord.Message) -> None:
        """Process commands on message."""
        if message.author == bot.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_error(self, context: Context, error) -> None:  # noqa: D103
        if isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="missing required argument",
                description=str(error).capitalize(),
                color=C_ERROR,
            )
            await context.send(embed=embed)

        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="no perms lmfao",
                description=f"required permission(s) `{', '.join(error.missing_permissions)}`",
                color=C_ERROR,
            )
            await context.send(embed=embed)

        elif isinstance(error, commands.NotOwner):
            embed = discord.Embed(title="not owner", description="no", color=C_ERROR)
            await context.send(embed=embed)

        elif isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours, minutes, seconds = int(hours), int(minutes), int(seconds)
            embed = discord.Embed(
                title="command on cooldown",
                description="cooldown expires in "
                + (f"{hours} hours " if hours > 0 else "")
                + (f"{minutes} minutes " if minutes > 0 else "")
                + (f"{seconds} seconds" if seconds > 0 else ""),
                color=C_ERROR,
            )
            await context.send(embed=embed)

        raise error


# @bot.event
# async def on_ready() -> None:  # noqa: D103
#     # start processes

#     bot.session: ClientSession = ClientSession(loop=bot.loop)  # type: ignore
#     bot.start_time: datetime = datetime.utcnow()  # type: ignore
#     print("loaded aiohttp session")
#     print("-------------------")
#     print(f"{bot.user.name}#{bot.user.discriminator}")  # type: ignore
#     print(f"discord.py {discord.__version__}")
#     print(f"Python {platform.python_version()}")
#     print(f"{platform.system()} {platform.release()} ({os.name})")
#     print("-------------------")
#     status_task.start()


# @tasks.loop(minutes=1.0)
# async def status_task() -> None:  # noqa: D103
#     statuses = ["beep boop im a bot"]
#     await bot.change_presence(activity=discord.Game(random.choice(statuses)))


# @bot.event
# async def on_message(message: discord.Message) -> None:  # noqa: D103
#     if message.author == bot.user or message.author.bot:
#         return
#     await bot.process_commands(message)


# @bot.event
# async def on_command_error(context: Context, error) -> None:  # noqa: D103
#     if isinstance(error, commands.MissingRequiredArgument):
#         embed = discord.Embed(
#             title="missing required argument",
#             description=str(error).capitalize(),
#             color=C_ERROR,
#         )
#         await context.send(embed=embed)

#     elif isinstance(error, commands.MissingPermissions):
#         embed = discord.Embed(
#             title="no perms lmfao",
#             description=f"required permission(s) `{', '.join(error.missing_permissions)}`",
#             color=C_ERROR,
#         )
#         await context.send(embed=embed)

#     elif isinstance(error, commands.NotOwner):
#         embed = discord.Embed(title="not owner", description="no", color=C_ERROR)
#         await context.send(embed=embed)

#     elif isinstance(error, commands.CommandOnCooldown):
#         minutes, seconds = divmod(error.retry_after, 60)
#         hours, minutes = divmod(minutes, 60)
#         hours, minutes, seconds = int(hours), int(minutes), int(seconds)
#         embed = discord.Embed(
#             title="command on cooldown",
#             description="cooldown expires in "
#             + (f"{hours} hours " if hours > 0 else "")
#             + (f"{minutes} minutes " if minutes > 0 else "")
#             + (f"{seconds} seconds" if seconds > 0 else ""),
#             color=C_ERROR,
#         )
#         await context.send(embed=embed)

#     raise error


# async def load_cogs() -> None:  # noqa: D103
#     for file in os.listdir("./bot/exts"):
#         if file.endswith(".py"):
#             ext = file[:-3]
#             try:
#                 await bot.load_extension(f"exts.{ext}")
#                 print(f"'{ext}' loaded")
#             except Exception as e:
#                 exception = f"{type(e).__name__}: {e}"
#                 print(f"Exception on loading {ext}\n{exception}")


# asyncio.run(load_cogs())

bot = Primed(command_prefix=commands.when_mentioned_or(PREFIX), intents=intents)
bot.run(TOKEN)  # type: ignore
