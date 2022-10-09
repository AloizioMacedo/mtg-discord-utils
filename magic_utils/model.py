from sqlalchemy import JSON, BigInteger, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

from env import POSTGRES_CONNECTION_URL

Base = declarative_base()

engine = create_engine(POSTGRES_CONNECTION_URL)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger)
    name = Column(String)
    deck = Column(JSON)


class Card(Base):
    __tablename__ = "card"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    card_attrs = Column(JSON)


Base.metadata.create_all(engine)
