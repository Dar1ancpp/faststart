import logging

from sqlmodel import Session, select

from app.models.game import Game
from app.models.listing import Listing, ListingBase
from app.schemas.listing import ListingCreate

logger = logging.getLogger(__name__)


class ListingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, listing_data: ListingCreate | ListingBase, owner_id: int
    ) -> Listing:
        try:
            if isinstance(listing_data, ListingCreate):
                data_dict = listing_data.model_dump()
                data_dict["owner_id"] = owner_id
                listing = Listing(**data_dict)
            else:
                listing = Listing.model_validate(listing_data)
                listing.owner_id = owner_id
            self.db.add(listing)
            self.db.commit()
            self.db.refresh(listing)
            return listing
        except Exception as e:
            logger.error(f"Error creating listing: {e}")
            self.db.rollback()
            raise

    def get_by_id(self, listing_id: int) -> Listing | None:
        return self.db.get(Listing, listing_id)

    def get_all(self, platform: str | None = None) -> list[tuple[Listing, Game]]:
        statement = select(Listing, Game).where(Listing.game_id == Game.id)
        if platform:
            statement = statement.where(Game.platform == platform)
        return self.db.exec(statement).all()

    def update_availability(
        self, listing_id: int, availability: str
    ) -> Listing | None:
        listing = self.db.get(Listing, listing_id)
        if not listing:
            return None
        listing.availability = availability
        self.db.add(listing)
        self.db.commit()
        self.db.refresh(listing)
        return listing
