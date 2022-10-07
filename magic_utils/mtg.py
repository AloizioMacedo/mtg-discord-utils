import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Union, cast

import aiohttp
import discord
from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from model import User, engine
from search import search_for_cards

SCRYFALL_URL = "https://api.scryfall.com"


class ValidCommandName(Enum):
    find_dual = "find_dual"
    get_rulings = "get_rulings"
    commands = "commands"
    get_card = "get_card"
    create_deck = "create_deck"
    search_deck = "search_deck"


# forest, island, mountain, plains, swamp

LANDS: dict[tuple[str, str], str] = {
    ("forest", "island"): "tropical island",
    ("forest", "mountain"): "taiga",
    ("forest", "plains"): "savannah",
    ("forest", "swamp"): "bayou",
    ("island", "mountain"): "volcanic island",
    ("island", "plains"): "tundra",
    ("island", "swamp"): "underground sea",
    ("mountain", "plains"): "plateau",
    ("mountain", "swamp"): "badlands",
    ("plains", "swamp"): "scrubland",
}


@dataclass(frozen=True)
class CardInfo:
    name: str
    small_url: str
    normal_url: str


def command_with_help(process_command: Callable) -> Callable:
    async def wrapper(*args):
        args = cast(tuple[CommandStrategy, discord.Message, str], args)
        if args[2] == "--help":
            await args[0].show_help(args[1])
        else:
            return await process_command(*args)

    return wrapper


class CommandStrategy(ABC):
    command: ValidCommandName

    @abstractmethod
    async def show_help(self, message: discord.Message) -> None:
        ...

    @abstractmethod
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> Union[list[CardInfo], list[str]]:
        ...


class FindDualLand(CommandStrategy):
    command = ValidCommandName.find_dual

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{land_types}")

    @command_with_help
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> list[CardInfo]:
        types = tuple(sorted([x.lower() for x in rest_of_command.split()]))

        if len(types) == 2:
            async with aiohttp.ClientSession() as session:
                response = await session.get(
                    url=f"{SCRYFALL_URL}/cards/named?exact={LANDS[types]}"
                )
                if response.status != 200:
                    raise ValueError

                card = await response.json()

            # card: mtgsdk.Card = mtgsdk.Card.where(name=LANDS[types]).all()[0]
            return [
                CardInfo(
                    card["name"],
                    small_url=card["image_uris"]["small"],
                    normal_url=card["image_uris"]["normal"],
                )
            ]

        elif len(types) == 1:
            all_pairs = [pair for pair in LANDS if types[0] in pair]
            tasks: list[asyncio.Task] = []
            async with aiohttp.ClientSession() as session:
                for pair in all_pairs:
                    tasks.append(asyncio.create_task(_get_dual(pair, session)))

                cards_info: list[CardInfo] = await asyncio.gather(*tasks)
            return cards_info

        else:
            return []


class GetRulings(CommandStrategy):
    command = ValidCommandName.get_rulings

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{card_name}")

    @command_with_help
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> list[str]:
        card_name = rest_of_command

        rulings: list[str] = []

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f'{SCRYFALL_URL}/cards/named?fuzzy="{card_name}"'
            )
            if response.status == 404:
                await message.channel.send("Card not found.")
                raise ValueError
            elif response.status != 200:
                raise ValueError

            card = await response.json()
            card_id = card["id"]
            rulings.append(f"Rulings for {card['name']}:")

            response = await session.get(
                f"{SCRYFALL_URL}/cards/{card_id}/rulings"
            )
            if response.status == 404:
                await message.channel.send("Ruling not found.")
                raise ValueError
            elif response.status != 200:
                raise ValueError

            json = await response.json()
            data: list[dict[str, str]] = json["data"]
            for i, entry in enumerate(data):
                rulings.append(
                    f"{i+1}. Ruling published at {entry['published_at']}:"
                    f" {entry['comment']}"
                )

        return rulings


class GetCard(CommandStrategy):
    command = ValidCommandName.get_card

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{card_name}")

    @command_with_help
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> list[CardInfo]:
        card_name = rest_of_command

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f'{SCRYFALL_URL}/cards/named?fuzzy="{card_name}"'
            )
            if response.status == 404:
                await message.channel.send("Card not found.")
                raise ValueError
            elif response.status != 200:
                raise ValueError

            card = await response.json()

        return [
            CardInfo(
                card["name"],
                card["image_uris"]["small"],
                card["image_uris"]["normal"],
            )
        ]


class ListCommands(CommandStrategy):
    command = ValidCommandName.commands

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self))

    @command_with_help
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> Union[list[CardInfo], list[str]]:
        if rest_of_command:
            await message.channel.send("Invalid syntax.")
            raise ValueError

        return ["Available commands:"] + [
            command.value for command in ValidCommandName
        ]


class CreateDeck(CommandStrategy):
    command = ValidCommandName.create_deck

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(
            _build_help(self) + "\n{MTG_ARENA_DECK_LIST}"
        )

    @command_with_help
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> Union[list[CardInfo], list[str]]:
        potential_card_names = [
            x.lower().strip() for x in rest_of_command.split("\n")
        ]
        cards_with_quantities = [
            x.split(maxsplit=1) for x in potential_card_names
        ]
        card_names: list[str] = []
        for card_with_quantity in cards_with_quantities:
            try:
                int(card_with_quantity[0])
                card_names.append(card_with_quantity[1])
            except:
                continue

        cards = search_for_cards(card_names)
        author = message.author

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()

            if result:
                result = cast(User, result)
                result.deck = {"deck": cards}  # type: ignore

            else:
                new_user = User(
                    discord_id=author.id,
                    name=author.name,
                    deck={"deck": cards},
                )
                session.add(new_user)

            session.commit()

        return [f"Deck with {len(card_names)} succesfully uploaded."]


class SearchDeck(CommandStrategy):
    command = ValidCommandName.search_deck

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{keyword}")

    @command_with_help
    async def process_command(
        self, message: discord.Message, rest_of_command: str
    ) -> Union[list[CardInfo], list[str]]:
        author = message.author
        text_query = rest_of_command.lower()

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()

            if result:
                result = cast(User, result)

            else:
                return ["Could not find a deck."]

            cards: list[dict] = result.deck["deck"]  # type: ignore

        query_results = [
            card
            for card in cards
            if fuzz.partial_ratio(
                text_query, card.get("oracle_text", "").lower()
            )
            > 90
        ]

        return [
            CardInfo(
                card["name"],
                card["image_uris"]["small"],
                card["image_uris"]["normal"],
            )
            for card in query_results
        ]


async def _get_dual(
    types: tuple[str, str], session: aiohttp.ClientSession
) -> CardInfo:
    response = await session.get(
        url=f"{SCRYFALL_URL}/cards/named?exact={LANDS[types]}"
    )
    if response.status != 200:
        raise ValueError

    card = await response.json()
    return CardInfo(
        card["name"],
        small_url=card["image_uris"]["small"],
        normal_url=card["image_uris"]["normal"],
    )


def _build_help(strategy: CommandStrategy) -> str:
    return f"Syntax:\n${strategy.command.value} "


COMMANDS: dict[ValidCommandName, CommandStrategy] = {
    ValidCommandName.find_dual: FindDualLand(),
    ValidCommandName.get_rulings: GetRulings(),
    ValidCommandName.commands: ListCommands(),
    ValidCommandName.get_card: GetCard(),
    ValidCommandName.create_deck: CreateDeck(),
    ValidCommandName.search_deck: SearchDeck(),
}
