import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Union

import aiohttp
import discord

SCRYFALL_URL = "https://api.scryfall.com"


class ValidCommandName(Enum):
    find_dual = "find_dual"
    get_rulings = "get_rulings"


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
    """"""

    @abstractmethod
    async def process_command(
        self, message: discord.Message, rest_of_command: list[str]
    ) -> Union[list[CardInfo], list[str]]:
        ...


class FindDualLand(CommandStrategy):
    """"""

    async def process_command(
        self, message: discord.Message, rest_of_command: list[str]
    ) -> list[CardInfo]:
        types = tuple(sorted([x.lower() for x in rest_of_command]))

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
    """"""

    async def process_command(
        self, message: discord.Message, rest_of_command: list[str]
    ) -> list[str]:
        card_name = " ".join(rest_of_command).lower().strip()

        rulings: list[str] = []

        async with aiohttp.ClientSession() as session:
            response = await session.get(
                f'{SCRYFALL_URL}/cards/named?exact="{card_name}"'
            )
            if response.status != 200:
                raise ValueError
            elif response.status == 404:
                await message.channel.send("Card not found.")
                raise ValueError

            card = await response.json()
            card_id = card["id"]
            rulings.append(f"Rulings for {card['name']}:")

            response = await session.get(
                f"{SCRYFALL_URL}/cards/{card_id}/rulings"
            )
            if response.status != 200:
                raise ValueError
            elif response.status == 404:
                await message.channel.send("Ruling not found.")
                raise ValueError

            json = await response.json()
            data: list[dict[str, str]] = json["data"]
            for i, entry in enumerate(data):
                rulings.append(
                    f"{i+1}. Ruling published at {entry['published_at']}:"
                    f" {entry['comment']}"
                )

        return rulings


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


COMMANDS: dict[ValidCommandName, CommandStrategy] = {
    ValidCommandName.find_dual: FindDualLand(),
    ValidCommandName.get_rulings: GetRulings(),
}
