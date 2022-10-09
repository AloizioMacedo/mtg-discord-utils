import json
from pathlib import Path

from sqlalchemy.orm import Session

from model import Card, engine
from search import treat_string

PARENT = Path(__file__).parent

CARDS_1_DB = PARENT.joinpath("oracle-cards-1.json")
CARDS_2_DB = PARENT.joinpath("oracle-cards-2.json")
CARDS_3_DB = PARENT.joinpath("oracle-cards-3.json")


def _get_cards() -> list[dict]:
    all_cards: list[dict[str, str]] = []

    with open(CARDS_1_DB) as file:
        all_cards += json.load(file)

    with open(CARDS_2_DB) as file:
        all_cards += json.load(file)

    with open(CARDS_3_DB) as file:
        all_cards += json.load(file)

    keys = ["name", "image_uris", "oracle_text"]

    return [{key: card.get(key, "") for key in keys} for card in all_cards]


def _populate_db(cards: list[dict]):
    with Session(engine) as session:
        session.add_all(
            [
                Card(name=treat_string(card["name"]), card_attrs=card)
                for card in cards
            ]
        )
        session.commit()


def main():
    _populate_db(_get_cards())


if __name__ == "__main__":
    main()
