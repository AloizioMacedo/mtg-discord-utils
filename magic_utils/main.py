import discord

from discord_token import TOKEN
from mtg import COMMANDS, CardInfo, ValidCommandName

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)


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
        message_tuple = message.content[1::].split()
        try:
            command = ValidCommandName(message_tuple[0])
        except ValueError:
            await message.channel.send("This command is not valid.")
            raise ValueError

        cards_info = await COMMANDS[command].process_command(
            message_tuple[1::]
        )

        return await send_cards(message, cards_info)


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


client.run(TOKEN)
