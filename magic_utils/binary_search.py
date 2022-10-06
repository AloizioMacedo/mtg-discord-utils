import json
from bisect import bisect_left
from pathlib import Path

PARENT = Path(__file__).parent

SORTED_CARDS_DB = PARENT.joinpath("sorted-cards.json")


def search_for_cards(names: list[str]) -> list[dict]:
    cards_list: list[dict] = []
    names = [name.strip().lower() for name in names]

    with open(SORTED_CARDS_DB) as file:
        all_cards: list[dict[str, str]] = json.load(file)
        all_cards_names = [card["name"].strip().lower() for card in all_cards]
        for name in names:
            card: dict[str, str] = all_cards[
                bisect_left(all_cards_names, name)
            ]
            if card["name"].strip().lower() != name:
                raise ValueError("Weird name.")

            cards_list.append(card)

    return cards_list
