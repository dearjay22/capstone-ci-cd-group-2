import pytest
from unittest.mock import patch, MagicMock
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client_obj:
        yield client_obj


@pytest.fixture
def mock_db():
    with patch("app.get_db") as mock:
        db = MagicMock()
        cursor = MagicMock()
        db.cursor.return_value = cursor
        mock.return_value = db
        yield db, cursor


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "healthy"


def test_list_orders_success(client, mock_db):
    """Test listing all orders"""
    db, cursor = mock_db
    cursor.fetchall.return_value = [
        {
            "id": 1,
            "user_id": 1,
            "product_id": 1,
            "quantity": 2,
            "status": "created",
            "total_price": 19.98,
            "created_at": "2024-01-01",
            "user_name": "John",
            "product_name": "Widget",
        }
    ]

    response = client.get("/orders")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["id"] == 1


def test_create_order_success(client, mock_db):
    """Test creating an order successfully"""
    db, cursor = mock_db

    # Mock user check
    cursor.fetchone.side_effect = [
        {"id": 1},  # User exists
        {"id": 1, "price": 9.99},  # Product exists with price
    ]
    cursor.lastrowid = 1

    response = client.post(
        "/orders",
        json={
            "user_id": 1,
            "product_id": 1,
            "quantity": 2,
        },
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["id"] == 1
    assert data["total_price"] == 19.98


def test_create_order_missing_user_id(client):
    """Test creating an order without user_id"""
    response = client.post(
        "/orders",
        json={
            "product_id": 1,
            "quantity": 2,
        },
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_create_order_missing_product_id(client):
    """Test creating an order without product_id"""
    response = client.post(
        "/orders",
        json={
            "user_id": 1,
            "quantity": 2,
        },
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_create_order_invalid_quantity(client):
    """Test creating an order with invalid quantity"""
    response = client.post(
        "/orders",
        json={
            "user_id": 1,
            "product_id": 1,
            "quantity": 0,
        },
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_create_order_user_not_found(client, mock_db):
    """Test creating an order with non-existent user"""
    db, cursor = mock_db
    cursor.fetchone.return_value = None

    response = client.post(
        "/orders",
        json={"user_id": 999, "product_id": 1, "quantity": 1},
    )
    assert response.status_code == 404
    data = response.get_json()
    assert "User not found" in data["error"]


def test_create_order_product_not_found(client, mock_db):
    """Test creating an order with non-existent product"""
    db, cursor = mock_db
    cursor.fetchone.side_effect = [
        {"id": 1},  # User exists
        None,  # Product doesn't exist
    ]

    response = client.post(
        "/orders",
        json={"user_id": 1, "product_id": 999, "quantity": 1},
    )
    assert response.status_code == 404
    data = response.get_json()
    assert "Product not found" in data["error"]


def test_get_order_success(client, mock_db):
    """Test getting a specific order"""
    db, cursor = mock_db
    cursor.fetchone.return_value = {
        "id": 1,
        "user_id": 1,
        "product_id": 1,
        "quantity": 2,
        "status": "created",
        "total_price": 19.98,
        "created_at": "2024-01-01",
        "user_name": "John",
        "product_name": "Widget",
    }

    response = client.get("/orders/1")
    assert response.status_code == 200
    data = response.get_json()
    assert data["id"] == 1


def test_get_order_not_found(client, mock_db):
    """Test getting a non-existent order"""
    db, cursor = mock_db
    cursor.fetchone.return_value = None

    response = client.get("/orders/999")
    assert response.status_code == 404


def test_get_orders_for_user_success(client, mock_db):
    """Test getting all orders for a user"""
    db, cursor = mock_db
    cursor.fetchall.return_value = [
        {
            "id": 1,
            "user_id": 1,
            "product_id": 1,
            "quantity": 2,
            "status": "created",
            "total_price": 19.98,
            "created_at": "2024-01-01",
            "product_name": "Widget",
            "product_price": 9.99,
        }
    ]

    response = client.get("/orders/user/1")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]["user_id"] == 1


def test_get_orders_for_user_empty(client, mock_db):
    """Test getting orders for user with no orders"""
    db, cursor = mock_db
    cursor.fetchall.return_value = []

    response = client.get("/orders/user/1")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0


def test_update_order_status_success(client, mock_db):
    """Test updating order status successfully"""
    db, cursor = mock_db
    cursor.rowcount = 1

    response = client.put("/orders/1/status", json={"status": "shipped"})
    assert response.status_code == 200
    data = response.get_json()
    assert "message" in data
    assert data["status"] == "shipped"


def test_update_order_status_missing_status(client):
    """Test updating order status without status field"""
    response = client.put("/orders/1/status", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_update_order_status_invalid_status(client):
    """Test updating order with invalid status"""
    response = client.put("/orders/1/status", json={"status": "invalid_status"})
    assert response.status_code == 400
    data = response.get_json()
    assert "Invalid status" in data["error"]


def test_update_order_status_not_found(client, mock_db):
    """Test updating status for non-existent order"""
    db, cursor = mock_db
    cursor.rowcount = 0

    response = client.put("/orders/999/status", json={"status": "shipped"})
    assert response.status_code == 404
