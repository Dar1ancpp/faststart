
from app.models.game import Game
from app.models.listing import Listing
from app.models.payment import Payment
from app.models.rental import Rental
from app.repositories.game import GameRepository
from app.repositories.listing import ListingRepository
from app.repositories.payment import PaymentRepository
from app.repositories.rental import RentalRepository
from app.schemas.game import GameCreate, GameResponse
from app.schemas.listing import ListingCreate, ListingResponse


class Staff:
    """Domain helper class for staff operations in unit tests."""

    @staticmethod
    def create_listing(
        owner, game, condition: str = "New", price: float = 0.0
    ) -> Listing:
        owner_id = getattr(owner, "id", owner)
        game_id = getattr(game, "id", game)
        return Listing(
            game_id=game_id,
            owner_id=owner_id,
            condition=condition,
            availability="Available",
            price=price,
        )


class GameService:
    def __init__(
        self,
        game_repo: GameRepository,
        listing_repo: ListingRepository,
        rental_repo: RentalRepository,
        payment_repo: PaymentRepository,
    ):
        self.game_repo = game_repo
        self.listing_repo = listing_repo
        self.rental_repo = rental_repo
        self.payment_repo = payment_repo

    def add_game(self, game_data: GameCreate) -> Game:
        return self.game_repo.create(game_data)

    def create_listing(self, owner_id: int, listing_data: ListingCreate) -> Listing:
        game = self.game_repo.get_by_id(listing_data.game_id)
        if not game:
            raise ValueError(f"Game with id {listing_data.game_id} does not exist.")
        return self.listing_repo.create(listing_data, owner_id=owner_id)

    def get_listings(
        self, platform: str | None = None
    ) -> list[ListingResponse]:
        results = self.listing_repo.get_all(platform=platform)
        listings_with_games = []
        for listing, game in results:
            game_resp = GameResponse(
                id=game.id,
                title=game.title,
                platform=game.platform,
                genre=game.genre,
                rating=game.rating,
                boxart=game.boxart,
            )
            listings_with_games.append(
                ListingResponse(
                    id=listing.id,
                    game_id=listing.game_id,
                    owner_id=listing.owner_id,
                    condition=listing.condition,
                    availability=listing.availability,
                    price=listing.price,
                    game=game_resp,
                )
            )
        return listings_with_games

    def create_rental(self, listing_id: int, customer_id: int) -> Rental:
        listing = self.listing_repo.get_by_id(listing_id)
        if not listing or listing.availability != "Available":
            raise ValueError("Listing is unavailable or does not exist.")

        rental = self.rental_repo.create(listing_id=listing_id, renter_id=customer_id)
        self.listing_repo.update_availability(listing_id, "Rented")
        return rental

    def return_rental(
        self,
        rental_id: int,
        payment_id: int | None = None,
        amount: float | None = None,
    ) -> Rental:
        rental = self.rental_repo.get_by_id(rental_id)
        if not rental:
            raise ValueError(f"Rental with id {rental_id} does not exist.")

        updated_rental = self.rental_repo.return_rental(rental_id)
        self.listing_repo.update_availability(rental.listing_id, "Available")

        if amount is not None and amount > 0:
            pay = self.payment_repo.create(amount=amount, customer_id=rental.renter_id)
            self.payment_repo.link_rental_payment(rental_id, pay.id)
        elif payment_id:
            self.payment_repo.link_rental_payment(rental_id, payment_id)

        return updated_rental

    def sell_listing(self, owner_id: int, listing_id: int) -> tuple[Listing, Payment]:
        listing = self.listing_repo.get_by_id(listing_id)
        if not listing:
            raise ValueError(f"Listing with id {listing_id} not found.")
        if listing.owner_id != owner_id:
            raise PermissionError("User is not the owner of this listing.")
        if listing.availability != "Available":
            raise ValueError("Listing is not available for sale.")

        updated_listing = self.listing_repo.update_availability(listing_id, "Sold")
        payment = self.payment_repo.create(amount=listing.price, customer_id=owner_id)
        return updated_listing, payment

    def process_payment(self, amount: float, customer_id: int | None = None) -> Payment:
        return self.payment_repo.create(amount=amount, customer_id=customer_id)
