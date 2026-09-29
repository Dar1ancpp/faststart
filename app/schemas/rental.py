
from sqlmodel import SQLModel


class RentalCreate(SQLModel):
    listing_id: int
    customer_id: int


class RentalUpdate(SQLModel):
    payment_id: int | None = None
    payment: float | None = None


class RentalResponse(SQLModel):
    id: int
    listing_id: int
    renter_id: int
    rental_date: str
    return_date: str | None = None
