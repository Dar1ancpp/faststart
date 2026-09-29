import logging
from datetime import date

from sqlmodel import Session

from app.models.payment import Payment, RentalPayment

logger = logging.getLogger(__name__)


class PaymentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, amount: float, customer_id: int | None = None) -> Payment:
        try:
            payment = Payment(
                customer_id=customer_id,
                payment_date=str(date.today()),
                amount=amount,
            )
            self.db.add(payment)
            self.db.commit()
            self.db.refresh(payment)
            return payment
        except Exception as e:
            logger.error(f"Error creating payment: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, payment_id: int) -> Payment | None:
        return self.db.get(Payment, payment_id)

    def link_rental_payment(self, rental_id: int, payment_id: int) -> RentalPayment:
        rp = RentalPayment(rental_id=rental_id, payment_id=payment_id)
        self.db.add(rp)
        self.db.commit()
        self.db.refresh(rp)
        return rp
