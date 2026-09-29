

def test_api_signup_and_duplicate_error(client):
    # Success case
    resp = client.post(
        "/signup",
        json={"username": "newuser", "email": "newuser@example.com", "password": "password123"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "newuser"

    # Duplicate case
    resp_dup = client.post(
        "/signup",
        json={"username": "newuser", "email": "other@example.com", "password": "password123"},
    )
    assert resp_dup.status_code == 400


def test_api_auth_success_and_failure(client):
    # Setup user
    client.post(
        "/signup",
        json={"username": "authuser", "email": "auth@example.com", "password": "mypassword"},
    )

    # Success case
    resp = client.post(
        "/auth",
        json={"username": "authuser", "password": "mypassword"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # Invalid password case
    resp_bad = client.post(
        "/auth",
        json={"username": "authuser", "password": "wrongpassword"},
    )
    assert resp_bad.status_code == 400


def test_api_games_create(client):
    resp = client.post(
        "/games",
        json={"title": "Super Mario Odyssey", "platform": "NSW", "genre": "Platformer", "rating": "E"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] is not None
    assert data["title"] == "Super Mario Odyssey"


def test_api_listings_create_and_get(client):
    # Signup owner
    client.post("/signup", json={"username": "gameowner", "email": "go@ex.com", "password": "secretpass"})
    auth_resp = client.post("/auth", json={"username": "gameowner", "password": "secretpass"})
    token = auth_resp.json()["access_token"]

    # Create game
    game_resp = client.post("/games", json={"title": "Metroid Dread", "platform": "NSW"})
    game_id = game_resp.json()["id"]

    # Protected listing creation without token -> 401
    no_auth_resp = client.post("/listings", json={"game_id": game_id, "condition": "New", "price": 59.99})
    assert no_auth_resp.status_code == 401

    # Protected listing creation with token -> 201
    auth_headers = {"Authorization": f"Bearer {token}"}
    create_resp = client.post(
        "/listings",
        json={"game_id": game_id, "condition": "New", "price": 59.99},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    assert create_resp.json()["game"]["title"] == "Metroid Dread"

    # Get listings by platform filter -> 200
    get_resp = client.get("/listings?platform=NSW")
    assert get_resp.status_code == 200
    assert len(get_resp.json()) >= 1


def test_api_payment(client):
    resp = client.post("/payment", json={"amount": 29.99})
    assert resp.status_code == 201
    data = resp.json()
    assert "paymentId" in data
    assert data["amount"] == 29.99


def test_api_rentals_and_return_workflow(client):
    # Setup owner and renter
    client.post("/signup", json={"username": "owner5", "email": "o5@ex.com", "password": "pass"})
    client.post("/signup", json={"username": "renter5", "email": "r5@ex.com", "password": "pass"})

    auth_owner = client.post("/auth", json={"username": "owner5", "password": "pass"}).json()
    client.post("/auth", json={"username": "renter5", "password": "pass"})

    game = client.post("/games", json={"title": "Halo Infinite", "platform": "XBOX"}).json()
    listing = client.post(
        "/listings",
        json={"game_id": game["id"], "condition": "Good", "price": 40.0},
        headers={"Authorization": f"Bearer {auth_owner['access_token']}"},
    ).json()

    # Create rental
    rental_resp = client.post("/rentals", json={"listing_id": listing["id"], "customer_id": 2})
    assert rental_resp.status_code == 201
    rental_id = rental_resp.json()["id"]

    # Return rental
    return_resp = client.put(f"/rentals/{rental_id}", json={"payment": 10.0})
    assert return_resp.status_code == 201
    assert return_resp.json()["return_date"] is not None


def test_api_sell_listing(client):
    # Setup owner and other user
    client.post("/signup", json={"username": "seller", "email": "seller@ex.com", "password": "pass"})
    client.post("/signup", json={"username": "buyer", "email": "buyer@ex.com", "password": "pass"})

    token_seller = client.post("/auth", json={"username": "seller", "password": "pass"}).json()["access_token"]
    token_buyer = client.post("/auth", json={"username": "buyer", "password": "pass"}).json()["access_token"]

    game = client.post("/games", json={"title": "God of War", "platform": "PS5"}).json()
    listing = client.post(
        "/listings",
        json={"game_id": game["id"], "condition": "Mint", "price": 45.0},
        headers={"Authorization": f"Bearer {token_seller}"},
    ).json()

    # Non-owner attempt to sell -> 403
    resp_forbidden = client.post(
        f"/listings/{listing['id']}/sell",
        headers={"Authorization": f"Bearer {token_buyer}"},
    )
    assert resp_forbidden.status_code == 403

    # Owner sell -> 200
    resp_sold = client.post(
        f"/listings/{listing['id']}/sell",
        headers={"Authorization": f"Bearer {token_seller}"},
    )
    assert resp_sold.status_code == 200
    assert resp_sold.json()["availability"] == "Sold"
