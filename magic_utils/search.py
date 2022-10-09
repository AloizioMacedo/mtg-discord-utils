import json
from pathlib import Path
from typing import cast

from sqlalchemy.orm import Session

from model import Card, engine
from string_treatment import treat_string

PARENT = Path(__file__).parent

CARDS_1_DB = PARENT.joinpath("oracle-cards-1.json")
CARDS_2_DB = PARENT.joinpath("oracle-cards-2.json")
CARDS_3_DB = PARENT.joinpath("oracle-cards-3.json")


def _get_cards_hashmap():
    all_cards: list[dict[str, str]] = []

    with open(CARDS_1_DB) as file:
        all_cards += json.load(file)

    with open(CARDS_2_DB) as file:
        all_cards += json.load(file)

    with open(CARDS_3_DB) as file:
        all_cards += json.load(file)

    keys = ["name", "image_uris", "oracle_text"]

    return {
        treat_string(card["name"]): {key: card.get(key, "") for key in keys}
        for card in all_cards
    }


CARD_HASHMAP = _get_cards_hashmap()


def search_for_card_ids(names: list[str]) -> list[int]:
    cards_list: list[int] = []
    treated_names = [treat_string(name) for name in names]

    with Session(engine) as session:
        for name in treated_names:
            q = session.query(Card).filter_by(name=treat_string(name))
            card = q.first()

            if card is None:
                raise ValueError(f"Weird name: {name}")

            card = cast(Card, card)
            cards_list.append(card.id)  # type: ignore

    return cards_list
