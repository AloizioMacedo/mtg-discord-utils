import json
from pathlib import Path

from string_treatment import treat_string

PARENT = Path(__file__).parent

CARDS_1_DB = PARENT.joinpath("oracle-cards-1.json")
CARDS_2_DB = PARENT.joinpath("oracle-cards-2.json")
CARDS_3_DB = PARENT.joinpath("oracle-cards-3.json")

all_cards: list[dict[str, str]] = []

with open(CARDS_1_DB) as file:
    all_cards += json.load(file)

with open(CARDS_2_DB) as file:
    all_cards += json.load(file)

with open(CARDS_3_DB) as file:
    all_cards += json.load(file)

CARD_HASHMAP = {treat_string(card["name"]): card for card in all_cards}


def search_for_cards(names: list[str]) -> list[dict]:
    cards_list: list[dict] = []
    treated_names = [treat_string(name) for name in names]

    for name in treated_names:
        card: dict[str, str] = CARD_HASHMAP[name]
        if treat_string(card["name"]) != name:
            raise ValueError(f"Weird name: {card['name']}")

        cards_list.append(card)

    return cards_list
