import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable, Union, cast
from uuid import uuid4

import aiohttp
import discord
from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from tabulate import tabulate

from command_decorator import commands
from env import FUZZY_THRESHOLD
from model import Card, Deck, User, engine
from search import search_for_card_ids

SCRYFALL_URL = "https://api.scryfall.com"


class ValidCommandName(Enum):
    find_dual = "find_dual"
    get_rulings = "get_rulings"
    commands = "commands"
    get_card = "get_card"
    create_deck = "create_deck"
    search_deck = "search_deck"
    list_decks = "list_decks"
    select_deck = "select_deck"
    rename_deck = "rename_deck"


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


class CommandStrategy(ABC):
    command: ValidCommandName

    @abstractmethod
    async def show_help(self, message: discord.Message) -> None:
        ...

    @commands
    @abstractmethod
    async def process_command(
        self, message: discord.Message, main: str, *args
    ) -> Union[list[CardInfo], list[str]]:
        ...


class FindDualLand(CommandStrategy):
    command = ValidCommandName.find_dual

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{land_types}")

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> list[CardInfo]:
        if help:
            await self.show_help(message)
            return []

        types = tuple(sorted([x.lower() for x in main.split()]))

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

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> list[str]:
        if help:
            await self.show_help(message)
            return []

        card_name = main

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

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> list[CardInfo]:
        if help:
            await self.show_help(message)
            return []

        card_name = main

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

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> Union[list[CardInfo], list[str]]:
        if help:
            await self.show_help(message)
            return []

        if main:
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

    @commands
    async def process_command(
        self,
        message: discord.Message,
        main: str,
        help: bool = False,
        name: str = "",
    ) -> Union[list[CardInfo], list[str]]:
        if help:
            await self.show_help(message)
            return []

        if not name:
            name = str(uuid4())

        potential_card_names = [x.lower().strip() for x in main.split("\n")]
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

        cards = search_for_card_ids(card_names)
        author = message.author

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()

            if result:
                result = cast(User, result)
                decks: list[Deck] = result.decks

                if len(decks) >= 3:
                    sorted_by_time: list[Deck] = sorted(
                        decks, key=lambda x: x.timestamp  # type: ignore
                    )
                    sorted_by_time.append(
                        Deck(
                            name=name,
                            user_id=result.id,
                            deck={"deck": cards},
                            timestamp=time.time(),
                        )
                    )
                    result.decks = sorted_by_time
                else:
                    decks.append(
                        Deck(
                            name=name,
                            user_id=result.id,
                            deck={"deck": cards},
                            timestamp=time.time(),
                        )
                    )

            else:
                new_user = User(
                    discord_id=author.id,
                    name=author.name,
                )
                new_user.decks = [
                    Deck(
                        name=name,
                        user_id=new_user.id,
                        deck={"deck": cards},
                        timestamp=time.time(),
                    )
                ]
                session.add(new_user)

            session.commit()

        return [f"Deck with {len(card_names)} succesfully uploaded."]


class ListDecks(CommandStrategy):
    command = ValidCommandName.search_deck

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self))

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> Union[list[CardInfo], list[str]]:
        if help:
            await self.show_help(message)
            return []

        author = message.author
        text_query = main.lower()

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()

            if result:
                result = cast(User, result)

            else:
                return ["Could not find decks for this user."]

            decks: list[Deck] = result.decks
            decks = sorted(decks, key=lambda x: x.timestamp)  # type: ignore
            return [
                tabulate(
                    [[f"{deck.id}", f"{deck.name}"] for deck in decks],
                    headers=["id", "name"],
                )
            ]


class SelectDeck(CommandStrategy):
    command = ValidCommandName.search_deck

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{DECK_ID}")

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> Union[list[CardInfo], list[str]]:
        if help:
            await self.show_help(message)
            return []

        selected_deck_id = int(main)

        author = message.author

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()

            if result:
                result = cast(User, result)

            else:
                return ["Could not find decks for this user."]

            decks: list[Deck] = result.decks
            if selected_deck_id not in [deck.id for deck in decks]:
                return ["The user does not have a deck with that ID."]

            else:
                result.selected_deck_id = selected_deck_id
                session.commit()
                return ["Deck selected."]


class RenameDeck(CommandStrategy):
    command = ValidCommandName.search_deck

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{NEW_NAME}")

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> Union[list[CardInfo], list[str]]:
        if help:
            await self.show_help(message)
            return []

        author = message.author

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()

            if result:
                result = cast(User, result)

            else:
                return ["Could not find decks for this user."]

            selected_deck_id = result.selected_deck_id

            if selected_deck_id is None:
                return [
                    "Please, select a deck with"
                    f" ${ValidCommandName.select_deck.value}"
                ]
            decks: list[Deck] = result.decks
            for deck in decks:
                if deck.id == selected_deck_id:
                    deck.name = main  # type: ignore
                    session.commit()
                    return ["Deck renamed successfully."]

            return ["Deck to be renamed could not be found anymore."]


class SearchDeck(CommandStrategy):
    command = ValidCommandName.search_deck

    async def show_help(self, message: discord.Message) -> None:
        await message.channel.send(_build_help(self) + "{keyword}")

    @commands
    async def process_command(
        self, message: discord.Message, main: str, help: bool = False
    ) -> Union[list[CardInfo], list[str]]:
        if help:
            await self.show_help(message)
            return []

        author = message.author
        text_query = main.lower()

        with Session(engine) as session:
            query = session.query(User).filter(User.discord_id == author.id)
            result = query.first()
            if result:
                result = cast(User, result)
            else:
                return ["Could not find a deck."]

            q = session.query(Deck).filter(
                Deck.user_id == result.id, Deck.id == result.selected_deck_id
            )

            deck_result = q.first()
            if deck_result:
                deck_result = cast(Deck, deck_result)
            else:
                return ["User does not have a deck selected."]

            cards: list[int] = deck_result.deck["deck"]  # type: ignore

            q: Iterable[Card] = session.query(Card).filter(Card.id.in_(cards))

            card_attrs: list[dict] = [
                card.card_attrs for card in q
            ]  # type: ignore

            query_results = [
                card_json
                for card_json in card_attrs
                if fuzz.partial_ratio(
                    text_query, card_json.get("oracle_text", "").lower()
                )
                > FUZZY_THRESHOLD
            ]

        if query_results:
            return [
                CardInfo(
                    card_json["name"],
                    card_json["image_uris"]["small"],
                    card_json["image_uris"]["normal"],
                )
                for card_json in query_results
            ]
        else:
            return ["No match was found."]


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
    ValidCommandName.select_deck: SelectDeck(),
    ValidCommandName.search_deck: SearchDeck(),
    ValidCommandName.list_decks: ListDecks(),
    ValidCommandName.rename_deck: RenameDeck(),
}
