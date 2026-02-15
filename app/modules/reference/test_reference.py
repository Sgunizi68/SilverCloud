"""
Reference Domain Tests
Unit tests for CRUD operations
"""

import pytest
from app import create_app
from app.common.database import db
from app.modules.auth.security import create_access_token
from datetime import timedelta


@pytest.fixture
def app():
    """Create test app instance."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def token(app):
    """Create valid JWT token for testing."""
    secret_key = app.config.get('SECRET_KEY')
    return create_access_token(
        data={"sub": "testuser"},
        secret_key=secret_key,
        expires_delta=timedelta(hours=24)
    )


class TestSubeEndpoints:
    """Test Sube (branch) endpoints."""
    
    def test_list_suber_requires_auth(self, client):
        """Test that list requires authentication."""
        response = client.get('/api/v1/subeler')
        assert response.status_code == 401
    
    def test_list_suber_with_auth(self, client, token):
        """Test listing branches with valid token."""
        response = client.get(
            '/api/v1/subeler',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
    
    def test_create_sube(self, client, token):
        """Test creating a new branch."""
        response = client.post(
            '/api/v1/subeler',
            json={'Sube_Adi': 'Test Şube', 'Aciklama': 'Test'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['Sube_Adi'] == 'Test Şube'
    
    def test_create_sube_missing_required(self, client, token):
        """Test creating branch without required fields."""
        response = client.post(
            '/api/v1/subeler',
            json={'Aciklama': 'Test'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 400


class TestKategoriEndpoints:
    """Test Kategori (category) endpoints."""
    
    def test_list_kategoriler_with_auth(self, client, token):
        """Test listing categories."""
        response = client.get(
            '/api/v1/kategoriler',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
    
    def test_kategoriler_pagination(self, client, token):
        """Test category pagination."""
        response = client.get(
            '/api/v1/kategoriler?skip=0&limit=10',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
    
    def test_kategoriler_filtering(self, client, token):
        """Test category filtering by type."""
        response = client.get(
            '/api/v1/kategoriler?tip=Gelir',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200


class TestUstKategoriEndpoints:
    """Test UstKategori (parent category) endpoints."""
    
    def test_list_ust_kategoriler(self, client, token):
        """Test listing parent categories."""
        response = client.get(
            '/api/v1/ust-kategoriler',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
    
    def test_create_ust_kategori(self, client, token):
        """Test creating parent category."""
        response = client.post(
            '/api/v1/ust-kategoriler',
            json={'UstKategori_Adi': 'Test Parent'},
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data['UstKategori_Adi'] == 'Test Parent'


class TestDegerEndpoints:
    """Test Deger (value) endpoints."""
    
    def test_list_degerler(self, client, token):
        """Test listing values."""
        response = client.get(
            '/api/v1/degerler',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
    
    def test_list_degerler_filtering(self, client, token):
        """Test filtering values by name."""
        response = client.get(
            '/api/v1/degerler?deger_adi=TestValue',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200


class TestKullaniciEndpoints:
    """Test Kullanici (user) endpoints."""
    
    def test_list_kullanicilar(self, client, token):
        """Test listing users."""
        response = client.get(
            '/api/v1/kullanicilar',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
    
    def test_list_kullanicilar_pagination(self, client, token):
        """Test user pagination."""
        response = client.get(
            '/api/v1/kullanicilar?skip=0&limit=5',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200


class TestEndpointSecurity:
    """Test endpoint security and error handling."""
    
    def test_missing_auth_header(self, client):
        """Test request without Authorization header."""
        response = client.get('/api/v1/kategoriler')
        assert response.status_code == 401
        assert 'error' in response.get_json()
    
    def test_invalid_token(self, client):
        """Test request with invalid token."""
        response = client.get(
            '/api/v1/kategoriler',
            headers={'Authorization': 'Bearer invalid.token.here'}
        )
        assert response.status_code == 401
    
    def test_wrong_bearer_format(self, client):
        """Test wrong Authorization header format."""
        response = client.get(
            '/api/v1/kategoriler',
            headers={'Authorization': 'InvalidFormat token'}
        )
        assert response.status_code == 401
