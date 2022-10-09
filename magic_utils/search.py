from typing import cast

from sqlalchemy.orm import Session

from model import Card, engine
from string_treatment import treat_string


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
