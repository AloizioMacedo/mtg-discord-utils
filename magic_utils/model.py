from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

from env import POSTGRES_CONNECTION_URL

Base = declarative_base()

engine = create_engine(POSTGRES_CONNECTION_URL)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger)
    name = Column(String)
    selected_deck_id = Column(Integer)

    decks = relationship(
        "Deck", back_populates="user", cascade="all, delete-orphan"
    )


class Card(Base):
    __tablename__ = "card"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    card_attrs = Column(JSON)


class Deck(Base):
    __tablename__ = "deck"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    name = Column(String)
    deck = Column(JSON)
    timestamp = Column(BigInteger)

    user = relationship("User", back_populates="decks")


Base.metadata.create_all(engine)
