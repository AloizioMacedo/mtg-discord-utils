import json
from pathlib import Path

PARENT = Path(__file__).parent
CARDS_DB = PARENT.joinpath("oracle-cards.json")
SORTED_CARDS_DB = PARENT.joinpath("sorted-cards.json")


def main():
    with open(CARDS_DB) as file:
        cards: list[dict] = json.load(file)
        cards.sort(key=lambda x: x["name"].lower())

    with open(SORTED_CARDS_DB, "w") as file:
        json.dump(cards, file)


if __name__ == "__main__":
    main()
