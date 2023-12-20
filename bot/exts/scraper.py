"""Scrape data of newly posted stats and sets from the front page of hsqb."""

from datetime import datetime

import discord
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from lib.consts import C_NEUTRAL, INVITE, HSQB
from typing import List, TypedDict

import aiohttp
from bs4 import BeautifulSoup

class StatReport:
    def __init__(self, name: str = None, link:str = None):
        self.name: str = name
        self.link: str = link

class TournamentStats:
    def __init__(self,
                 tournament_name: str = None,
                 tournament_link: str = None,
                 stat_reports: List[StatReport] = None):
        self.tournament_name: str = tournament_name
        self.tournament_link: str = tournament_link
        self.stat_reports: List[StatReport] = stat_reports

    def __str__(self):
        return f"{self.tournament_name} ({self.tournament_link})" + "\n" + "\n".join([f"\t{sr.name} ({sr.link})" for sr in self.stat_reports])

class Set:
    def __init__(self, name: str = None, link: str = None):
        self.name: str = name
        self.link: str = link

    def __str__(self):
        return f"{self.name} ({self.link})"

class Cache(TypedDict):
    stats: List[TournamentStats]
    sets: List[Set]

class Scraper(commands.Cog, name="scraper commands"):
    """Command class for scraping hsqb data."""

    mock_webpage = False

    cache: Cache = {"stats": [], "sets": []}

    def __init__(self, bot: Bot):
        self.bot = bot

    async def get_page(self) -> BeautifulSoup:
        """Get HTML page from the front page of hsqb."""
        if self.mock_webpage:
            with open("webpages/sample.html") as f:
                return BeautifulSoup(f.read(), "html.parser")
        async with self.bot.session.get(HSQB) as response:
            return BeautifulSoup(await response.text(), "html.parser")

    def parse_page(self, soup: BeautifulSoup) -> Cache:
        """Parse BeautifulSoup into a list of stats and sets."""
        stats_div = soup.find(id="RecentStats")
        tournaments = stats_div.find("ul", class_="Tournaments").find_all("li", recursive=False)
        scraped_stats = []

        for tournament in tournaments:
            tournament_name: str = str(tournament.find("span", class_="Tournament").find("a").string)
            tournament_link: str = HSQB + str(tournament.find("span", class_="Tournament").find("a")["href"])
            stat_reports = [StatReport(name=str(report.find("a").string),
                                    link=HSQB + str(report.find("a")["href"]))
                                    for report in tournament.find("ul", class_="Reports").find_all("li")]
            scraped_stats.append(TournamentStats(tournament_name=tournament_name,
                                                tournament_link=tournament_link,
                                                stat_reports=stat_reports))

        sets_div = soup.find(id="RecentlyPostedSets")
        sets = sets_div.find("ul", class_="NoHeader").find_all("li", recursive=False)
        scraped_sets = []

        for set in sets:
            set_name: str = str(set.find("span", class_="Name").find("a").string)
            set_link: str = HSQB + str(set.find("span", class_="Name").find("a")["href"])
            scraped_sets.append(Set(name=set_name, link=set_link))

        return {"stats": scraped_stats, "sets": scraped_sets}


    @tasks.loop(seconds=20)
    async def scrape(self) -> None:
        """Scrape data."""
        print("attempting to scrape")
        soup = await self.get_page()
        stats, sets = self.parse_page(soup).values()
        for stat in stats:
            print(stat)
        for set in sets:
            print(set)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print("starting scrape loop")
        self.scrape.start()

async def setup(bot):  # noqa: D103
    await bot.add_cog(Scraper(bot))
