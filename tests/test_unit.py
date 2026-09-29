from types import SimpleNamespace
import pytest
from pydantic import ValidationError

from app.models.user import User
from app.schemas.listing import ListingCreate
from app.services.game_service import GameService, Staff
from app.utilities.security import encrypt_password, verify_password


def test_new_user():
    newuser = User(username="bob", email="bob@example.com", password="bobpass")
    assert newuser.username == "bob"
    assert newuser.email == "bob@example.com"


def test_toJSON():
    newuser = User(username="bob", email="bob@example.com", password="bobpass")
    user_json = newuser.model_dump()
    assert user_json["id"] is None
    assert user_json["username"] == "bob"


def test_hashed_password():
    hashed = encrypt_password("mypass")
    assert hashed != "mypass"


def test_check_password():
    hashed = encrypt_password("mypass")
    assert verify_password("mypass", hashed) is True
    assert verify_password("wrongpass", hashed) is False


def test_create_listing():
    owner = SimpleNamespace(id=10)
    game = SimpleNamespace(id=42)

    listing = Staff.create_listing(owner, game, condition="Mint", price=49.99)

    assert listing.owner_id == 10
    assert listing.game_id == 42
    assert listing.condition == "Mint"
    assert listing.availability == "Available"
    assert listing.price == 49.99


def test_schema_invalid_listing_condition():
    with pytest.raises(ValidationError):
        ListingCreate(game_id=1, condition="BrokenCondition", price=19.99)


def test_service_refuses_missing_or_unavailable_listing():
    class FakeListingRepo:
        def get_by_id(self, listing_id):
            if listing_id == 1:
                return SimpleNamespace(id=1, availability="Rented")
            return None

    service = GameService(
        game_repo=None,
        listing_repo=FakeListingRepo(),
        rental_repo=None,
        payment_repo=None,
    )

    with pytest.raises(ValueError, match="unavailable or does not exist"):
        service.create_rental(listing_id=1, customer_id=5)

    with pytest.raises(ValueError, match="unavailable or does not exist"):
        service.create_rental(listing_id=99, customer_id=5)
