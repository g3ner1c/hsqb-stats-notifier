"""Scrape data of newly posted stats and sets from the front page of hsqb."""

from datetime import datetime
from typing import List, Tuple

import aiohttp
import discord
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from discord.ext.commands import Bot, Context
from lib.consts import C_NEUTRAL, HSQB, INVITE


class StatReport:
    def __init__(self, name: str, link: str):
        self.name: str = name
        self.link: str = link

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, StatReport):
            return NotImplemented

        return self.name == __value.name and self.link == __value.link


class TournamentStats:
    def __init__(
        self,
        tournament_name: str,
        tournament_link: str,
        stat_reports: List[StatReport],
    ):
        self.tournament_name: str = tournament_name
        self.tournament_link: str = tournament_link
        self.stat_reports: List[StatReport] = stat_reports

    def __str__(self):
        return (
            f"{self.tournament_name} ({self.tournament_link})"
            + "\n"
            + "\n".join([f"\t{sr.name} ({sr.link})" for sr in self.stat_reports])
        )

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, TournamentStats):
            return NotImplemented

        return (
            self.tournament_name == __value.tournament_name
            and self.tournament_link == __value.tournament_link
            and self.stat_reports == __value.stat_reports
        )


class Set:
    def __init__(self, name: str, link: str):
        self.name: str = name
        self.link: str = link

    def __str__(self):
        return f"{self.name} ({self.link})"

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Set):
            return NotImplemented

        return self.name == __value.name and self.link == __value.link


class Scrape:
    def __init__(
        self, stats: List[TournamentStats], sets: List[Set], timestamp: datetime
    ):
        self.stats: List[TournamentStats] = stats
        self.sets: List[Set] = sets
        self.timestamp: datetime = timestamp


class Scraper(commands.Cog, name="scraper commands"):
    """Command class for scraping hsqb data."""

    mock_webpage: bool = False

    cache: Scrape | None = None
    scrape_cycle: int = 0

    def __init__(self, bot: Bot):
        self.bot = bot
        self.scrape_cycle = 0

    async def get_page(self) -> Tuple[BeautifulSoup, datetime]:
        """Get HTML page from the front page of hsqb."""
        if self.mock_webpage:
            with open("webpages/sample.html") as f:
                return BeautifulSoup(f.read(), "html.parser"), datetime.utcnow()
        async with self.bot.session.get(HSQB) as response:  # type: ignore
            return (
                BeautifulSoup(await response.text(), "html.parser"),
                datetime.utcnow(),
            )

    async def parse_page(self, soup: BeautifulSoup, timestamp: datetime) -> Scrape:
        """Parse BeautifulSoup into a list of stats and sets."""
        stats_div = soup.find(id="RecentStats")
        tournaments = stats_div.find("ul", class_="Tournaments").find_all(  # type: ignore
            "li", recursive=False
        )
        scraped_stats: List[TournamentStats] = []

        for tournament in tournaments:
            tournament_name: str = str(
                tournament.find("span", class_="Tournament").find("a").string
            )
            tournament_link: str = HSQB + str(
                tournament.find("span", class_="Tournament").find("a")["href"]
            )
            stat_reports = [
                StatReport(
                    name=str(report.find("a").string),
                    link=HSQB + str(report.find("a")["href"]),
                )
                for report in tournament.find("ul", class_="Reports").find_all("li")
            ]
            scraped_stats.append(
                TournamentStats(
                    tournament_name=tournament_name,
                    tournament_link=tournament_link,
                    stat_reports=stat_reports,
                )
            )

        sets_div = soup.find(id="RecentlyPostedSets")
        sets = sets_div.find("ul", class_="NoHeader").find_all(  # type: ignore
            "li", recursive=False
        )
        scraped_sets: List[Set] = []

        for set in sets:
            set_name: str = str(set.find("span", class_="Name").find("a").string)
            set_link: str = HSQB + str(
                set.find("span", class_="Name").find("a")["href"]
            )
            scraped_sets.append(Set(name=set_name, link=set_link))

        return Scrape(stats=scraped_stats, sets=scraped_sets, timestamp=timestamp)

    async def get_new(self, new_scrape: Scrape) -> Scrape | None:
        """Get new stats from a new scrape."""
        if self.cache is None:
            return None  # return None if there is no cache, first scrape will be used as cache
        return Scrape(
            stats=[
                tournament
                for tournament in new_scrape.stats
                if tournament not in self.cache.stats
            ],
            sets=[set for set in new_scrape.sets if set not in self.cache.sets],
            timestamp=new_scrape.timestamp,
        )

    @tasks.loop(seconds=20)
    async def scrape(self) -> None:
        """Scrape data."""
        print("attempting to scrape")
        soup, timestamp = await self.get_page()
        scraped_data = await self.parse_page(soup, timestamp)
        stats = scraped_data.stats
        sets = scraped_data.sets
        for stat in stats:
            print(stat)
        for set in sets:
            print(set)
        print(scraped_data.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        print("scrape complete")

        new_data = await self.get_new(scraped_data)  # newly posted stats and sets
        if new_data is None:
            print("no cache, setting cache")

        if new_data is not None:
            if len(new_data.stats) == 0 and len(new_data.sets) == 0:
                print("no new data")

            else:
                pass

        self.cache = scraped_data
        self.scrape_cycle += 1
        await self.bot.change_presence(activity=discord.Game(f"/help | @ cycle #{self.scrape_cycle}"))  # type: ignore

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        print("starting scrape loop")
        self.scrape.start()


async def setup(bot):  # noqa: D103
    await bot.add_cog(Scraper(bot))
