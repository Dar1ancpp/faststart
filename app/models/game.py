
from sqlmodel import Field, SQLModel


class GameBase(SQLModel):
    title: str = Field(index=True)
    rating: str = "E"
    platform: str = Field(index=True)  # NSW, PS5, XBOX, PC
    boxart: str = ""
    genre: str = ""


class Game(GameBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
