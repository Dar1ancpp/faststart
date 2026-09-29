# Evidence & Implementation Report: Game Rental API & Testing

**Repository URL:** [https://github.com/Dar1ancpp/faststart](https://github.com/Dar1ancpp/faststart)  
**Author / Student Name:** [Student Name]  
**Course:** COMP3613 — Web Software Technologies  
**Date:** September 29, 2026  
**Environment:** Python 3.13, FastAPI, SQLModel, SQLite, Pytest  

---

## Executive Summary

This report documents the implementation and comprehensive testing suite for the **Game Rental API** (Tutorial 4). The FastStart web application was extended from a basic user authentication starter into a multi-layered game rental system supporting games, listings, rentals, payments, and owner sale transactions.

The implementation strictly adheres to the layered architecture (Routes → Dependencies → Schemas → Services → Repositories → Models). All **21 unit, integration, and API tests** pass cleanly with 0 warnings.

---

## 1. Acceptance Test Plan (User Acceptance Testing)

### Question 1: Test Plan for "Test Sell Game"

| Test Case | Pre-conditions | Test Steps | Test Criteria | Success |
| :--- | :--- | :--- | :--- | :--- |
| **Test Sell Game** | • User logged in as an `Owner`<br>• User owns an active game listing (`availability == "Available"`) | 1. Navigate to "My Listings" / Game Details screen.<br>2. Select the game listing to sell to the store.<br>3. Click **"Sell Game to Store"** button.<br>4. Confirm sale details and price.<br>5. Click **"Confirm Sale"**. | • User is alerted/prompted that sale was successful.<br>• Listing availability status updates from `Available` to `Sold`.<br>• Store creates a payment credit record for the owner.<br>• Listing is removed from active marketplace listings. | **Pass** |

---

## 2. Unit Testing

### Question 2: Unit Testing for `Staff.create_listing()`

**Answer:** Yes, a unit test for `Staff.create_listing()` can be implemented without database dependencies by instantiating domain models directly or using mock objects for `owner` and `game`.

#### Unit Test Plan Table

| Unit Test | Module Tested | Expected Output |
| :--- | :--- | :--- |
| `test_new_user()` | `newuser = User("bob", "bobpass")` | `newuser.username == "bob"` |
| `test_toJSON()` | `User.to_json()` | `{"id": None, "username": "bob"}` |
| `test_hashed_password()` | `User.set_password("mypass")` | `newuser.password != "mypass"` |
| `test_check_password()` | `User.check_password("mypass")` | `True` |
| `test_create_listing()` | `Staff.create_listing(owner, game, condition="Mint", price=49.99)` | Returns `Listing` instance with `owner_id == owner.id`, `game_id == game.id`, `condition == "Mint"`, `availability == "Available"`, and `price == 49.99`. |
| `test_schema_invalid_listing_condition()` | `ListingCreate(game_id=1, condition="BrokenCondition", price=10.0)` | Raises `ValidationError` for invalid condition value. |
| `test_service_refuses_missing_or_unavailable_listing()` | `GameService.create_rental(listing_id=99, customer_id=1)` | Raises `ValueError` for missing or non-available listing. |

---

## 3. Integration Testing

### Question 3: Integration Test Table for Rental Confirmation & Returns

| Test | Dependencies | Description |
| :--- | :--- | :--- |
| `test_create_user()` | `create_user()`, `get_user()` | Ensures user record in database has correct values. |
| `test_authenticate()` | `create_user()`, `authenticate()` | Ensures `authenticate()` returns true when given correct credentials. |
| `test_get_all_users_json()` | `create_user()`, `get_all_users_json()` | Verifies JSON data of all users in the system. |
| `test_update_user()` | `create_user()`, `update_user()`, `get_user()` | Ensures an updated user is retrieved with updated values. |
| `test_staff_create_listing()` | `create_staff()`, `create_user()`, `create_game()`, `staff.create_listing()` | Lets staff create a game listing for a game a customer owns. Ensures listing record is created with staff, customer, and game IDs. |
| `test_staff_confirm_rental()` | `create_staff()`, `create_user()`, `create_listing()`, `create_rental()` | Lets staff confirm a game rental for a customer on an available listing. Ensures a `Rental` record is created, and listing availability changes to `"Rented"`. |
| `test_staff_return_rental()` | `create_staff()`, `create_rental()`, `create_payment()`, `return_rental()` | Lets staff process a return for a rented game. Ensures return date is recorded, payment is attached, and listing availability resets to `"Available"`. |
| `test_owner_can_sell_only_their_own_active_listing()` | `create_user()`, `create_listing()`, `sell_listing()` | Ensures owner can sell active listing (`"Sold"` status + payment creation) and prevents non-owner sale attempts. |

---

## 4. API Specification & Implementation

### Question 4: Game Rental API Endpoint Specification

| Access | Method | Path | Request Body | Success / Errors |
| :--- | :--- | :--- | :--- | :--- |
| **Public** | `POST` | `/signup` | `username`, `email`, `password` | `201` Account created; `400` Duplicate |
| **Public** | `POST` | `/auth` | `username`, `password` | `200` Token object; `400` Invalid credentials |
| **Customer** | `POST` | `/listings` | `game_id`, `condition`, `price` | `201` Listing created with nested game; `401` Unauthorized; `404` Bad game; `422` Bad condition |
| **Public** | `GET` | `/listings?platform=` | Query: `NSW` \| `PS5` \| `XBOX` \| `PC` | `200` Listed games with nested game data |
| **Staff** | `POST` | `/payment` | `amount`, `customer_id` | `201` Payment created + `paymentId` |
| **Staff** | `POST` | `/rentals` | `listing_id`, `customer_id` | `201` Rental created; `404` Bad/unavailable listing |
| **Staff** | `PUT` | `/rentals/{rental_id}` | `payment` or `payment_id` | `201` Rental return date updated; `404` Missing rental/payment |
| **Owner** | `POST` | `/listings/{listing_id}/sell` | Header: `Authorization: Bearer <token>` | `200` Listing marked `Sold` & payment credited; `403` Not owner; `404` Missing/unavailable listing |
| **Staff** | `POST` | `/games` | `title`, `platform`, `genre`, `rating`, `boxart` | `201` Game created |

---

## 5. Test Suite Execution & Evidence

### Test Suite Execution Command & Results

```bash
python -m pytest tests -v
```

```text
============================= test session starts =============================
platform win32 -- Python 3.13.1, pytest-9.1.1, pluggy-1.6.0
configfile: pytest.ini
collected 21 items

tests/test_api.py::test_api_signup_and_duplicate_error PASSED            [  4%]
tests/test_api.py::test_api_auth_success_and_failure PASSED              [  9%]
tests/test_api.py::test_api_games_create PASSED                          [ 14%]
tests/test_api.py::test_api_listings_create_and_get PASSED               [ 19%]
tests/test_api.py::test_api_payment PASSED                               [ 23%]
tests/test_api.py::test_api_rentals_and_return_workflow PASSED           [ 28%]
tests/test_api.py::test_api_sell_listing PASSED                          [ 33%]
tests/test_integration.py::test_save_password PASSED                     [ 38%]
tests/test_integration.py::test_login PASSED                             [ 42%]
tests/test_integration.py::test_register_user PASSED                     [ 47%]
tests/test_integration.py::test_create_game_and_listing_persists_with_ids PASSED [ 52%]
tests/test_integration.py::test_create_rental_changes_listing_to_rented PASSED [ 57%]
tests/test_integration.py::test_return_rental_records_payment_and_makes_listing_available PASSED [ 61%]
tests/test_integration.py::test_owner_can_sell_only_their_own_active_listing PASSED [ 66%]
tests/test_unit.py::test_password_hash_round_trip_and_rejects_wrong_password PASSED [ 71%]
tests/test_unit.py::test_authenticate_user_returns_token_for_valid_credentials PASSED [ 76%]
tests/test_unit.py::test_authenticate_user_returns_none_for_invalid_credentials PASSED [ 80%]
tests/test_unit.py::test_access_token_contains_subject_and_role PASSED   [ 85%]
tests/test_unit.py::test_create_listing PASSED                           [ 90%]
tests/test_unit.py::test_schema_invalid_listing_condition PASSED         [ 95%]
tests/test_unit.py::test_service_refuses_missing_or_unavailable_listing PASSED [100%]

============================= 21 passed in 4.35s ==============================
```

---

## 6. API Route Test Evidence Log

### 1. Account Registration (`POST /signup`)
- **Positive Case (201 Created):**
  - **Request:** `POST /signup` `{"username": "newuser", "email": "newuser@example.com", "password": "password123"}`
  - **Response (201):** `{"id": 3, "username": "newuser", "email": "newuser@example.com", "message": "Account created"}`
- **Negative Case (400 Duplicate):**
  - **Request:** `POST /signup` `{"username": "newuser", "email": "other@example.com", "password": "password123"}`
  - **Response (400):** `{"detail": "Duplicate username or email"}`

### 2. User Authentication (`POST /auth`)
- **Positive Case (200 OK):**
  - **Request:** `POST /auth` `{"username": "authuser", "password": "mypassword"}`
  - **Response (200):** `{"access_token": "<JWT_TOKEN>", "token_type": "bearer", "token": "<JWT_TOKEN>"}`
- **Negative Case (400 Invalid Credentials):**
  - **Request:** `POST /auth` `{"username": "authuser", "password": "wrongpassword"}`
  - **Response (400):** `{"detail": "Invalid credentials"}`

### 3. Create Game Listing (`POST /listings`)
- **Negative Case (401 Unauthorized):**
  - **Request:** `POST /listings` without Authorization header
  - **Response (401):** `{"detail": "Could not validate credentials"}`
- **Positive Case (201 Created):**
  - **Request:** `POST /listings` Header: `Authorization: Bearer <TOKEN>` Body: `{"game_id": 1, "condition": "New", "price": 59.99}`
  - **Response (201):** `{"id": 1, "game_id": 1, "owner_id": 3, "condition": "New", "availability": "Available", "price": 59.99, "game": {"id": 1, "title": "Metroid Dread", "platform": "NSW", "genre": "Action", "rating": "T", "boxart": ""}}`

### 4. Browse Listings (`GET /listings?platform=NSW`)
- **Positive Case (200 OK):**
  - **Request:** `GET /listings?platform=NSW`
  - **Response (200):** Array of active listings with nested game objects matching `platform == "NSW"`.

### 5. Create Rental (`POST /rentals`)
- **Positive Case (201 Created):**
  - **Request:** `POST /rentals` `{"listing_id": 1, "customer_id": 2}`
  - **Response (201):** `{"id": 1, "listing_id": 1, "renter_id": 2, "rental_date": "2026-09-29"}`
- **Negative Case (404 Unavailable Listing):**
  - **Request:** `POST /rentals` `{"listing_id": 1, "customer_id": 2}` (when listing availability is already `"Rented"`)
  - **Response (404):** `{"detail": "Listing is unavailable or does not exist."}`

### 6. Return Rental (`PUT /rentals/{rental_id}`)
- **Positive Case (201 Created):**
  - **Request:** `PUT /rentals/1` `{"payment": 10.0}`
  - **Response (201):** `{"id": 1, "listing_id": 1, "renter_id": 2, "return_date": "2026-09-29", "message": "Rental updated"}`

### 7. Owner Sell Listing (`POST /listings/{id}/sell`)
- **Negative Case (403 Forbidden):**
  - **Request:** `POST /listings/1/sell` with Non-Owner Bearer Token
  - **Response (403):** `{"detail": "User is not the owner of this listing."}`
- **Positive Case (200 OK):**
  - **Request:** `POST /listings/1/sell` with Owner Bearer Token
  - **Response (200):** `{"message": "Listing sold successfully", "listing_id": 1, "availability": "Sold", "payment_id": 2, "amount": 59.99}`

---

## 7. Postman Collection Verification

The Postman collection at [`postman/FastStarter.postman_collection.json`](file:///c:/Users/daria/Desktop/UWI/COMP3613/Tutorials%20Code/Tutorial%204/faststart/postman/FastStarter.postman_collection.json) has been updated for testing:

1. Import `postman/FastStarter.postman_collection.json` into Postman.
2. Set environment variable `baseUrl` to `http://127.0.0.1:5000`.
3. Execute `POST /auth` to receive access token.
4. Set Postman `Authorization` header to `Bearer <access_token>` for protected endpoints (`POST /listings`, `POST /listings/{id}/sell`).

---

## Conclusion

All requirements for **Tutorial 4: Testing & Game Rental API** have been completely implemented and verified. The codebase is clean, robust, fully tested, and ready for submission.
