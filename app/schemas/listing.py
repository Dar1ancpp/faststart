
from pydantic import field_validator
from sqlmodel import SQLModel

from app.schemas.game import GameResponse

ALLOWED_CONDITIONS = {"New", "Mint", "Good", "Fair", "Used"}


class ListingCreate(SQLModel):
    game_id: int
    condition: str
    price: float

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v not in ALLOWED_CONDITIONS:
            raise ValueError(
                f"Invalid listing condition: {v}. Must be one of {ALLOWED_CONDITIONS}"
            )
        return v


class ListingResponse(SQLModel):
    id: int
    game_id: int
    owner_id: int
    condition: str
    availability: str
    price: float
    game: GameResponse | None = None
