
from sqlmodel import SQLModel


class PaymentCreate(SQLModel):
    amount: float
    customer_id: int | None = None


class PaymentResponse(SQLModel):
    id: int
    customer_id: int | None = None
    payment_date: str
    amount: float
