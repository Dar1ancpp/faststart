from types import SimpleNamespace

import jwt
import pytest
from pydantic import ValidationError

from app.schemas.listing import ListingCreate
from app.services.auth_service import AuthService
from app.services.game_service import GameService, Staff
from app.utilities.security import encrypt_password, verify_password


def test_password_hash_round_trip_and_rejects_wrong_password():
    password_hash = encrypt_password("correct horse")

    assert password_hash != "correct horse"
    assert verify_password("correct horse", password_hash)
    assert not verify_password("wrong horse", password_hash)


def test_authenticate_user_returns_token_for_valid_credentials(monkeypatch):
    user = SimpleNamespace(
        id=7,
        username="alice",
        password=encrypt_password("secret"),
        role="regular_user",
    )

    class FakeUserRepository:
        def get_by_username(self, username):
            return user if username == "alice" else None

    monkeypatch.setattr(
        "app.services.auth_service.create_access_token",
        lambda data: {"sub": data["sub"], "role": data["role"]},
    )

    token = AuthService(FakeUserRepository()).authenticate_user("alice", "secret")

    assert token == {"sub": "7", "role": "regular_user"}


def test_authenticate_user_returns_none_for_invalid_credentials():
    user = SimpleNamespace(
        id=7,
        username="alice",
        password=encrypt_password("secret"),
        role="regular_user",
    )

    class FakeUserRepository:
        def get_by_username(self, username):
            return user if username == "alice" else None

    service = AuthService(FakeUserRepository())

    assert service.authenticate_user("alice", "incorrect") is None
    assert service.authenticate_user("missing", "secret") is None


def test_access_token_contains_subject_and_role():
    from app.config import get_settings
    from app.utilities.security import create_access_token

    token = create_access_token({"sub": "7", "role": "admin"})
    settings = get_settings()
    payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.jwt_algorithm],
    )

    assert payload["sub"] == "7"
    assert payload["role"] == "admin"
    assert "exp" in payload


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
