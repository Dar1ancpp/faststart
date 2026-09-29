
from sqlmodel import Field, SQLModel


class PaymentBase(SQLModel):
    customer_id: int | None = Field(default=None, foreign_key="user.id")
    payment_date: str
    amount: float


class Payment(PaymentBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class RentalPayment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    rental_id: int = Field(foreign_key="rental.id")
    payment_id: int = Field(foreign_key="payment.id")
