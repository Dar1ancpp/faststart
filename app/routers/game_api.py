
from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import SessionDep
from app.dependencies.auth import AuthDep
from app.repositories.game import GameRepository
from app.repositories.listing import ListingRepository
from app.repositories.payment import PaymentRepository
from app.repositories.rental import RentalRepository
from app.repositories.user import UserRepository
from app.schemas.auth import SigninRequest, SignupRequest
from app.schemas.game import GameCreate, GameResponse
from app.schemas.listing import ListingCreate, ListingResponse
from app.schemas.payment import PaymentCreate
from app.schemas.rental import RentalCreate, RentalUpdate
from app.services.auth_service import AuthService
from app.services.game_service import GameService

game_api_router = APIRouter()


def get_game_service(db: SessionDep) -> GameService:
    return GameService(
        game_repo=GameRepository(db),
        listing_repo=ListingRepository(db),
        rental_repo=RentalRepository(db),
        payment_repo=PaymentRepository(db),
    )


# 1. POST /signup (Public)
@game_api_router.post("/signup", status_code=status.HTTP_201_CREATED)
@game_api_router.post("/api/signup", status_code=status.HTTP_201_CREATED)
async def api_signup(req: SignupRequest, db: SessionDep):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    try:
        user = auth_service.register_user(req.username, req.email, req.password)
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "message": "Account created",
        }
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate username or email",
        )


# 2. POST /auth (Public)
@game_api_router.post("/auth")
@game_api_router.post("/api/auth")
async def api_auth(req: SigninRequest, db: SessionDep):
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    token = auth_service.authenticate_user(req.username, req.password)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials"
        )
    return {"access_token": token, "token_type": "bearer", "token": token}


# 3. POST /games (Staff / Development)
@game_api_router.post("/games", status_code=status.HTTP_201_CREATED)
@game_api_router.post("/api/games", status_code=status.HTTP_201_CREATED)
async def create_game(game_in: GameCreate, db: SessionDep):
    service = get_game_service(db)
    game = service.add_game(game_in)
    return game


# 4. POST /listings (Customer / Owner)
@game_api_router.post(
    "/listings",
    status_code=status.HTTP_201_CREATED,
    response_model=ListingResponse,
)
@game_api_router.post(
    "/api/listings",
    status_code=status.HTTP_201_CREATED,
    response_model=ListingResponse,
)
async def create_listing(
    listing_in: ListingCreate, current_user: AuthDep, db: SessionDep
):
    service = get_game_service(db)
    try:
        listing = service.create_listing(
            owner_id=current_user.id, listing_data=listing_in
        )
        game = service.game_repo.get_by_id(listing.game_id)
        game_resp = (
            GameResponse(
                id=game.id,
                title=game.title,
                platform=game.platform,
                genre=game.genre,
                rating=game.rating,
                boxart=game.boxart,
            )
            if game
            else None
        )
        return ListingResponse(
            id=listing.id,
            game_id=listing.game_id,
            owner_id=listing.owner_id,
            condition=listing.condition,
            availability=listing.availability,
            price=listing.price,
            game=game_resp,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# 5. GET /listings?platform= (Public)
@game_api_router.get("/listings", response_model=list[ListingResponse])
@game_api_router.get("/api/listings", response_model=list[ListingResponse])
async def get_listings(db: SessionDep, platform: str | None = Query(None)):
    service = get_game_service(db)
    return service.get_listings(platform=platform)


# 6. POST /payment (Staff)
@game_api_router.post("/payment", status_code=status.HTTP_201_CREATED)
@game_api_router.post("/api/payment", status_code=status.HTTP_201_CREATED)
async def create_payment(payment_in: PaymentCreate, db: SessionDep):
    service = get_game_service(db)
    pay = service.process_payment(
        amount=payment_in.amount, customer_id=payment_in.customer_id
    )
    return {
        "paymentId": pay.id,
        "amount": pay.amount,
        "customer_id": pay.customer_id,
        "payment_date": pay.payment_date,
    }


# 7. POST /rentals (Staff)
@game_api_router.post("/rentals", status_code=status.HTTP_201_CREATED)
@game_api_router.post("/api/rentals", status_code=status.HTTP_201_CREATED)
async def create_rental(rental_in: RentalCreate, db: SessionDep):
    service = get_game_service(db)
    try:
        rental = service.create_rental(
            listing_id=rental_in.listing_id, customer_id=rental_in.customer_id
        )
        return {
            "id": rental.id,
            "listing_id": rental.listing_id,
            "renter_id": rental.renter_id,
            "rental_date": rental.rental_date,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# 8. PUT /rentals/{rental_id} (Staff)
@game_api_router.put("/rentals/{rental_id}", status_code=status.HTTP_201_CREATED)
@game_api_router.put("/api/rentals/{rental_id}", status_code=status.HTTP_201_CREATED)
async def update_rental(rental_id: int, rental_up: RentalUpdate, db: SessionDep):
    service = get_game_service(db)
    try:
        rental = service.return_rental(
            rental_id=rental_id,
            payment_id=rental_up.payment_id,
            amount=rental_up.payment,
        )
        return {
            "id": rental.id,
            "listing_id": rental.listing_id,
            "renter_id": rental.renter_id,
            "return_date": rental.return_date,
            "message": "Rental updated",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# 9. POST /listings/{listing_id}/sell (Owner)
@game_api_router.post("/listings/{listing_id}/sell")
@game_api_router.post("/api/listings/{listing_id}/sell")
async def sell_listing(listing_id: int, current_user: AuthDep, db: SessionDep):
    service = get_game_service(db)
    try:
        listing, payment = service.sell_listing(
            owner_id=current_user.id, listing_id=listing_id
        )
        return {
            "message": "Listing sold successfully",
            "listing_id": listing.id,
            "availability": listing.availability,
            "payment_id": payment.id,
            "amount": payment.amount,
        }
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
