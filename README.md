MTG Utils is a discord bot for QOL funcionalities regarding Magic: The Gathering, such as:
- Consulting cards;
- Consulting rulings;
- Searching for cards with specified effects in a deck;
- etc

It uses [Scryfall](https://scryfall.com/) as an API for simple queries, and its data dump for queries that would require a lot of requests.

This is a non-profit project.

## How to use the bot

Use [this url](https://discord.com/api/oauth2/authorize?client_id=1027250946998272132&permissions=3088&scope=bot) to invite the bot to a server you manage. The bot needs just three permissions:

1. Manage Channels
2. Read Messages/View Channels
3. Send Messages

Permission (1.) is required for creating a channel dedicated for the bot commands. (The bot still works in other channels, this is just intended for organization.)
Permission (2.) is required for the bot to be able to see the messages, and (3.) in order to be able to respond to them.

### Commands:
You can get a list of all commands by using the command

```$commands```

Some basic help is available by just using the command appended with "--help". For example:

```$get_card --help```

At the moment, this help consists only of clarification of syntax. We intend to provide more explanation via this command in the future.

At the moment, we have the following commands:
- $find_dual: Finds the dual land(s) that enter the battlefield untapped given one or two land types. If only one is chosen, it returns the four respective dual lands. If two are chosen, it returns just the one.

    Syntax Examples:

    ```$find_dual island```

    ```$find_dual swamp mountain```
- $get_rulings: Finds rulings of a given specified card.

    Syntax Examples:

    ```$get_rulings Oko, Thief of Crowns```
- $commands: List all commands.
- $get_card: Finds a given card

    Syntax Examples:

    ```$get_card Sol Ring```
- $create_deck: Creates a deck by accepting MTGA format. Accepts an optional --name parameter that can be used to give a certain name to the deck to identify it. If this parameter is not used, it will generate a uuid4 as its name. OBS: There is a maximum of 3 decks per user at the moment. Once over this limit, it overwrites the oldest deck.

    Syntax Examples:

    ```
    $create_deck --name "Illegal Simple Red"
    1 Fervent Champion
    1 Mountain
    ```
- $search_deck: Searches your selected deck (see $select_deck) for a card that contains the specified string in its text. OBS: The search allows for some leeway on the spellings.

    Syntax Examples:

    ```$search_deck destroy target```
- $list_decks: List all current decks of the user making the command.
- $select_deck: Selects a deck (by its id) in order to be able to search on it and rename it.

    Syntax Examples:

    ```$select_deck 3```
- $rename_deck: Renames the selected deck (see $select_deck).

    Syntax Examples:

    ```$rename_deck "The deck I love the most"```


## Development

If you want to test the bot, you need to follow these steps:

1. Make a bot by going [here](https://discord.com/developers/applications/) and following the procedures;
2. Get its token and put it in an _env.py file as a variable named TOKEN;
3. Run the docker-compose.yaml file with docker-compose;
4. Run create_db.py in order to populate the database with the cards.

After this, just get your discord bot invite link (refer again to discord's [applications page](ttps://discord.com/developers/applications/)), invite it to a given server, and test it out!

## Suggestions/Criticism/Bugs/etc

If you have any issue with the bot, just open an [issue](https://github.com/AloizioMacedo/mtg-discord-utils/issues)! : )