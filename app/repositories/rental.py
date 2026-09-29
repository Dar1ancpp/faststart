import logging
from datetime import date

from sqlmodel import Session

from app.models.rental import Rental

logger = logging.getLogger(__name__)


class RentalRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, listing_id: int, renter_id: int) -> Rental:
        try:
            rental = Rental(
                listing_id=listing_id,
                renter_id=renter_id,
                rental_date=str(date.today()),
            )
            self.db.add(rental)
            self.db.commit()
            self.db.refresh(rental)
            return rental
        except Exception as e:
            logger.error(f"Error creating rental: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, rental_id: int) -> Rental | None:
        return self.db.get(Rental, rental_id)

    def return_rental(self, rental_id: int) -> Rental | None:
        rental = self.db.get(Rental, rental_id)
        if not rental:
            return None
        rental.return_date = str(date.today())
        self.db.add(rental)
        self.db.commit()
        self.db.refresh(rental)
        return rental
