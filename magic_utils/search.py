import json
import unicodedata
from pathlib import Path

PARENT = Path(__file__).parent

SORTED_CARDS_DB = PARENT.joinpath("sorted-cards.json")


def _strip_accents(s: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )


def _treat_string(s: str) -> str:
    return _strip_accents(s.split("//")[0].strip().lower())


with open(SORTED_CARDS_DB) as file:
    all_cards: list[dict[str, str]] = json.load(file)

CARD_HASHMAP = {_treat_string(card["name"]): card for card in all_cards}


def search_for_cards(names: list[str]) -> list[dict]:
    cards_list: list[dict] = []
    treated_names = [_treat_string(name) for name in names]

    for name in treated_names:
        card: dict[str, str] = CARD_HASHMAP[name]
        if _treat_string(card["name"]) != name:
            raise ValueError(f"Weird name: {card['name']}")

        cards_list.append(card)

    return cards_list
