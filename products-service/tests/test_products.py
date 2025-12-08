import pytest
from unittest.mock import Mock, patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    with patch('app.get_db') as mock:
        db = MagicMock()
        cursor = MagicMock()
        db.cursor.return_value = cursor
        mock.return_value = db
        yield db, cursor

def test_health_check(client):
    """Test health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_list_products_success(client, mock_db):
    """Test listing products successfully"""
    db, cursor = mock_db
    cursor.fetchall.return_value = [
        {'id': 1, 'name': 'Widget', 'price': 9.99, 'description': 'A widget', 'created_at': '2024-01-01'},
        {'id': 2, 'name': 'Gadget', 'price': 12.99, 'description': 'A gadget', 'created_at': '2024-01-02'}
    ]
    
    response = client.get('/products')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert data[0]['name'] == 'Widget'

def test_list_products_empty(client, mock_db):
    """Test listing products when database is empty"""
    db, cursor = mock_db
    cursor.fetchall.return_value = []
    
    response = client.get('/products')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 0

def test_get_product_success(client, mock_db):
    """Test getting a specific product"""
    db, cursor = mock_db
    cursor.fetchone.return_value = {
        'id': 1, 
        'name': 'Widget', 
        'price': 9.99, 
        'description': 'A widget',
        'created_at': '2024-01-01'
    }
    
    response = client.get('/products/1')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'Widget'

def test_get_product_not_found(client, mock_db):
    """Test getting a non-existent product"""
    db, cursor = mock_db
    cursor.fetchone.return_value = None
    
    response = client.get('/products/999')
    assert response.status_code == 404
    data = response.get_json()
    assert 'error' in data

def test_add_product_success(client, mock_db):
    """Test adding a product successfully"""
    db, cursor = mock_db
    cursor.lastrowid = 1
    
    response = client.post('/products', json={
        'name': 'New Product',
        'price': 19.99,
        'description': 'A new product'
    })
    assert response.status_code == 201
    data = response.get_json()
    assert data['id'] == 1
    assert 'message' in data

def test_add_product_missing_name(client):
    """Test adding a product without name"""
    response = client.post('/products', json={
        'price': 19.99
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_add_product_missing_price(client):
    """Test adding a product without price"""
    response = client.post('/products', json={
        'name': 'New Product'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_add_product_invalid_price(client):
    """Test adding a product with invalid price"""
    response = client.post('/products', json={
        'name': 'New Product',
        'price': 'not-a-number'
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_add_product_negative_price(client):
    """Test adding a product with negative price"""
    response = client.post('/products', json={
        'name': 'New Product',
        'price': -10.00
    })
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data

def test_update_product_success(client, mock_db):
    """Test updating a product successfully"""
    db, cursor = mock_db
    cursor.rowcount = 1
    
    response = client.put('/products/1', json={
        'name': 'Updated Product',
        'price': 25.99
    })
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_update_product_not_found(client, mock_db):
    """Test updating a non-existent product"""
    db, cursor = mock_db
    cursor.rowcount = 0
    
    response = client.put('/products/999', json={
        'name': 'Updated Product'
    })
    assert response.status_code == 404

def test_update_product_no_data(client):
    """Test updating a product with no data"""
    response = client.put('/products/1', json={})
    assert response.status_code == 400

def test_delete_product_success(client, mock_db):
    """Test deleting a product successfully"""
    db, cursor = mock_db
    cursor.rowcount = 1
    
    response = client.delete('/products/1')
    assert response.status_code == 200
    data = response.get_json()
    assert 'message' in data

def test_delete_product_not_found(client, mock_db):
    """Test deleting a non-existent product"""
    db, cursor = mock_db
    cursor.rowcount = 0
    
    response = client.delete('/products/999')
    assert response.status_code == 404