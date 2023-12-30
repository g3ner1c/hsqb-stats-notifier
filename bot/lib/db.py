"""Database utilies."""

from typing import Self

import discord
from consts import MONGODB_URI
from motor.motor_asyncio import AsyncIOMotorClient

schema = {
    "_id": str,
    "discord": {
        "id": int,
        "username": str,
        "global_name": str,
        "bot": bool,
        "system": bool,
        "dm_channel_id": int,
    },
    "preferences": {
        "stats": bool,
        "sets": bool,
    },
}


class DuplicateUserError(Exception):
    """Raised when a user already exists in the database."""

    pass


class User:
    def __init__(
        self,
        discord_id: int,
        username: str,
        global_name: str,
        bot: bool,
        system: bool,
        dm_channel_id: int,
        stats: bool = True,
        sets: bool = True,
    ):
        self.discord_id: int = discord_id
        self.username: str = username
        self.global_name: str = global_name
        self.bot: bool = bot
        self.system: bool = system
        self.dm_channel_id: int = dm_channel_id
        self.stats: bool = stats
        self.sets: bool = sets

    @classmethod
    async def from_discord_id(
        cls, discord_client: discord.Client, discord_id: int
    ) -> Self:
        user = discord_client.get_user(discord_id) or await discord_client.fetch_user(
            discord_id
        )
        return await cls.from_discord_user(user)

    @classmethod
    async def from_discord_user(cls, user: discord.User) -> Self:
        if user.dm_channel is None:
            dm_channel = await user.create_dm()
            dm_channel_id = dm_channel.id
        else:
            dm_channel_id = user.dm_channel.id

        return cls(
            discord_id=user.id,
            username=user.name,
            global_name=user.global_name or user.name,
            bot=user.bot,
            system=user.system,
            dm_channel_id=dm_channel_id,
        )

    @classmethod
    async def from_mongo_doc(cls, doc: dict) -> Self:
        return cls(
            discord_id=doc["discord"]["id"],
            username=doc["discord"]["username"],
            global_name=doc["discord"]["global_name"],
            bot=doc["discord"]["bot"],
            system=doc["discord"]["system"],
            dm_channel_id=doc["discord"]["dm_channel_id"],
            stats=doc["preferences"]["stats"],
            sets=doc["preferences"]["sets"],
        )

    async def to_mongo_doc(self) -> dict:
        return {
            "discord": {
                "id": self.discord_id,
                "username": self.username,
                "global_name": self.global_name,
                "bot": self.bot,
                "system": self.system,
                "dm_channel_id": self.dm_channel_id,
            },
            "preferences": {"stats": self.stats, "sets": self.sets},
        }

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, User):
            return NotImplemented

        return (
            self.discord_id
            == __value.discord_id
            # and self.username == __value.username
            # and self.global_name == __value.global_name
            # and self.bot == __value.bot
            # and self.system == __value.system
            # and self.dm_channel_id == __value.dm_channel_id
            # and self.stats == __value.stats
            # and self.sets == __value.sets
        )


class Database:
    def __init__(self, discord_client: discord.Client) -> None:
        self.discord_client = discord_client
        self.client = AsyncIOMotorClient(MONGODB_URI)
        self.db = self.client.primed
        self.users = self.db.users

    async def user_exists(self, discord_id: int) -> bool:
        return await self.users.find_one({"discord.id": discord_id}) is not None

    async def get_user(self, discord_id: int) -> User | None:
        doc = await self.users.find_one({"discord.id": discord_id})
        return await User.from_mongo_doc(doc) if doc else None

    async def get_all_users(self) -> list[User]:
        return [await User.from_mongo_doc(doc) async for doc in self.users.find()]

    async def add_user(self, user: User) -> None:
        if await self.user_exists(user.discord_id):
            raise DuplicateUserError(f"user {user.discord_id} already exists")
        await self.users.insert_one(await user.to_mongo_doc())

    async def update_user(self, user: User) -> None:
        await self.users.replace_one(
            {"discord.id": user.discord_id}, await user.to_mongo_doc()
        )

    async def delete_user(self, user: User) -> None:
        await self.users.delete_one({"discord.id": user.discord_id})

    async def check_for_duplicates(self) -> None:
        users = await self.get_all_users()
        duplicates = []
        for user in users:
            if users.count(user) > 1:
                duplicates.append(user)
        if duplicates:
            raise DuplicateUserError(
                f"found {len(duplicates)} duplicate(s): {duplicates}"
            )

    async def regenerate_user(self, discord_id: int) -> None:
        user = await User.from_discord_id(self.discord_client, discord_id)
        await self.update_user(user)

    async def regenerate_all_users(self) -> None:
        for user in await self.get_all_users():
            await self.regenerate_user(user.discord_id)

    async def close(self) -> None:
        self.client.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()
