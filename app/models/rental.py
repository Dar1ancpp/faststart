
from sqlmodel import Field, SQLModel


class RentalBase(SQLModel):
    listing_id: int = Field(foreign_key="listing.id")
    renter_id: int = Field(foreign_key="user.id")
    rental_date: str
    return_date: str | None = None


class Rental(RentalBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
