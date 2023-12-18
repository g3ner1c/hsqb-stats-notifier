"""Scrape data of newly posted stats and sets from the front page of hsqb."""

from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from lib.consts import C_NEUTRAL, INVITE, HSQB

import aiohttp
from bs4 import BeautifulSoup


class Scraper(commands.Cog, name="general commands"):
    """Command class for scraping hsqb data."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_page(self) -> BeautifulSoup:
        """Get HTML page from the front page of hsqb."""
        async with self.bot.session.get(HSQB) as response:
            return BeautifulSoup(await response.text(), "html.parser")


    @tasks.loop(minutes=3.0)
    async def scrape(self, ctx: Context) -> None:
        """Scrape data."""
        soup = await self.get_page()
        print(soup)



async def setup(bot):  # noqa: D103
    await bot.add_cog(Scraper(bot))
