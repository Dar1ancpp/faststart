
from sqlmodel import Field, SQLModel


class ListingBase(SQLModel):
    game_id: int = Field(foreign_key="game.id")
    owner_id: int = Field(foreign_key="user.id")
    condition: str = "New"
    availability: str = "Available"  # Available, Rented, Sold
    price: float = 0.0


class Listing(ListingBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
