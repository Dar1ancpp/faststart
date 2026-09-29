import jwt
import pytest

from app.config import get_settings
from app.repositories.game import GameRepository
from app.repositories.listing import ListingRepository
from app.repositories.payment import PaymentRepository
from app.repositories.rental import RentalRepository
from app.repositories.user import UserRepository
from app.schemas.game import GameCreate
from app.schemas.listing import ListingCreate
from app.schemas.user import RegularUserCreate
from app.services.auth_service import AuthService
from app.services.game_service import GameService
from app.services.user_service import UserService
from app.utilities.security import encrypt_password, verify_password


def test_save_password(test_session):
    repository = UserRepository(test_session)
    service = AuthService(repository)

    created = service.register_user("alice", "alice@example.com", "secret")
    saved = repository.get_by_username("alice")

    assert saved is not None
    assert created.id == saved.id
    assert saved.username == "alice"
    assert saved.email == "alice@example.com"
    assert saved.role == "regular_user"
    assert saved.password != "secret"
    assert verify_password("secret", saved.password)


def test_login(test_session):
    repository = UserRepository(test_session)
    service = AuthService(repository)
    service.register_user("alice", "alice@example.com", "secret")

    token = service.authenticate_user("alice", "secret")
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == str(repository.get_by_username("alice").id)
    assert payload["role"] == "regular_user"


def test_register_user(test_session):
    repository = UserRepository(test_session)
    auth_service = AuthService(repository)
    auth_service.register_user("alice", "alice@example.com", "secret")

    users = UserService(repository).get_all_users()

    assert len(users) == 1
    assert users[0].username == "alice"
    assert users[0].email == "alice@example.com"


def test_create_game_and_listing_persists_with_ids(test_session):
    user_repo = UserRepository(test_session)
    owner = user_repo.create(
        RegularUserCreate(
            username="owner1",
            email="owner1@example.com",
            password=encrypt_password("pass"),
        )
    )

    service = GameService(
        game_repo=GameRepository(test_session),
        listing_repo=ListingRepository(test_session),
        rental_repo=RentalRepository(test_session),
        payment_repo=PaymentRepository(test_session),
    )

    game = service.add_game(GameCreate(title="Elden Ring", platform="PS5", genre="RPG"))
    assert game.id is not None

    listing = service.create_listing(
        owner_id=owner.id,
        listing_data=ListingCreate(game_id=game.id, condition="New", price=69.99),
    )
    assert listing.id is not None
    assert listing.game_id == game.id
    assert listing.owner_id == owner.id
    assert listing.availability == "Available"


def test_create_rental_changes_listing_to_rented(test_session):
    user_repo = UserRepository(test_session)
    owner = user_repo.create(RegularUserCreate(username="owner2", email="o2@ex.com", password=encrypt_password("p")))
    renter = user_repo.create(RegularUserCreate(username="renter2", email="r2@ex.com", password=encrypt_password("p")))

    service = GameService(
        game_repo=GameRepository(test_session),
        listing_repo=ListingRepository(test_session),
        rental_repo=RentalRepository(test_session),
        payment_repo=PaymentRepository(test_session),
    )

    game = service.add_game(GameCreate(title="Zelda", platform="NSW", genre="Action"))
    listing = service.create_listing(owner.id, ListingCreate(game_id=game.id, condition="Mint", price=50.0))

    rental = service.create_rental(listing_id=listing.id, customer_id=renter.id)

    assert rental.id is not None
    assert rental.listing_id == listing.id
    assert rental.renter_id == renter.id

    updated_listing = service.listing_repo.get_by_id(listing.id)
    assert updated_listing.availability == "Rented"


def test_return_rental_records_payment_and_makes_listing_available(test_session):
    user_repo = UserRepository(test_session)
    owner = user_repo.create(RegularUserCreate(username="owner3", email="o3@ex.com", password=encrypt_password("p")))
    renter = user_repo.create(RegularUserCreate(username="renter3", email="r3@ex.com", password=encrypt_password("p")))

    service = GameService(
        game_repo=GameRepository(test_session),
        listing_repo=ListingRepository(test_session),
        rental_repo=RentalRepository(test_session),
        payment_repo=PaymentRepository(test_session),
    )

    game = service.add_game(GameCreate(title="Halo", platform="XBOX", genre="FPS"))
    listing = service.create_listing(owner.id, ListingCreate(game_id=game.id, condition="Used", price=30.0))
    rental = service.create_rental(listing.id, renter.id)

    returned_rental = service.return_rental(rental_id=rental.id, amount=15.0)

    assert returned_rental.return_date is not None
    updated_listing = service.listing_repo.get_by_id(listing.id)
    assert updated_listing.availability == "Available"


def test_owner_can_sell_only_their_own_active_listing(test_session):
    user_repo = UserRepository(test_session)
    owner = user_repo.create(RegularUserCreate(username="owner4", email="o4@ex.com", password=encrypt_password("p")))
    other_user = user_repo.create(RegularUserCreate(username="other", email="oth@ex.com", password=encrypt_password("p")))

    service = GameService(
        game_repo=GameRepository(test_session),
        listing_repo=ListingRepository(test_session),
        rental_repo=RentalRepository(test_session),
        payment_repo=PaymentRepository(test_session),
    )

    game = service.add_game(GameCreate(title="Mario Kart", platform="NSW", genre="Racing"))
    listing = service.create_listing(owner.id, ListingCreate(game_id=game.id, condition="New", price=50.0))

    # Non-owner cannot sell
    with pytest.raises(PermissionError):
        service.sell_listing(owner_id=other_user.id, listing_id=listing.id)

    # Owner can sell
    sold_listing, payment = service.sell_listing(owner_id=owner.id, listing_id=listing.id)
    assert sold_listing.availability == "Sold"
    assert payment.amount == 50.0

    # Cannot sell already sold listing
    with pytest.raises(ValueError, match="not available"):
        service.sell_listing(owner_id=owner.id, listing_id=listing.id)
