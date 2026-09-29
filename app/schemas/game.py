from sqlmodel import SQLModel


class GameCreate(SQLModel):
    title: str
    platform: str
    genre: str = ""
    rating: str = "E"
    boxart: str = ""


class GameResponse(SQLModel):
    id: int
    title: str
    platform: str
    genre: str
    rating: str
    boxart: str
