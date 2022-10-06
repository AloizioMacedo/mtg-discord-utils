from sqlalchemy import JSON, BigInteger, Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base

from env import POSTGRES_SERVICE

Base = declarative_base()

engine = create_engine(
    f"postgresql://postgres:postgres@{POSTGRES_SERVICE}/postgres"
)


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    discord_id = Column(BigInteger)
    name = Column(String)
    deck = Column(JSON)


Base.metadata.create_all(engine)
