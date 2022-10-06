import json
from pathlib import Path

from string_treatment import treat_string

PARENT = Path(__file__).parent

SORTED_CARDS_DB = PARENT.joinpath("oracle-cards.json")


with open(SORTED_CARDS_DB) as file:
    all_cards: list[dict[str, str]] = json.load(file)

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
