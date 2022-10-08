from typing import cast

import discord

from client import client
from env import TOKEN
from mtg import COMMANDS, CardInfo, ValidCommandName


@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")
    guilds: list[discord.Guild] = list(client.guilds)

    for guild in guilds:
        channels = guild.channels
        if "mtg-utils" not in [channel.name for channel in channels]:
            await guild.create_text_channel("mtg-utils")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if message.content.startswith("$"):
        message_tuple = message.content[1::].split(maxsplit=1)
        try:
            command = ValidCommandName(message_tuple[0])
        except ValueError:
            await message.channel.send("This command is not valid.")
            raise ValueError

        if len(message_tuple) == 2:
            rest_of_command = message_tuple[1].strip()
        else:
            rest_of_command = ""

        result = await COMMANDS[command].process_command(
            message, rest_of_command
        )

        if not result:
            return

        if isinstance(result[0], CardInfo):
            result = cast(list[CardInfo], result)
            return await send_cards(message, result)

        elif isinstance(result[0], str):
            result = cast(list[str], result)
            return await send_message(message, result)


async def send_cards(message: discord.Message, cards_info: list[CardInfo]):
    if len(cards_info) == 1:
        card_info = cards_info[0]
        await message.channel.send(card_info.normal_url)

    elif len(cards_info) <= 4:
        await message.channel.send(
            "\n".join([card_info.small_url for card_info in cards_info])
        )

    else:
        await message.channel.send(", ".join(card.name for card in cards_info))


async def send_message(message: discord.Message, content: list[str]):
    n = len(content)
    for i in range(0, n, 4):
        await message.channel.send(
            "\n".join([strng for strng in content[i : i + 4]])
        )


client.run(TOKEN)
