import pytest
from django.urls import reverse
from django.test import Client
from django.db import connection
from app.views import get_db_connection


@pytest.fixture
def django_db_setup(django_db_setup, django_db_blocker):
    # Ensures database setup for pytest
    with django_db_blocker.unblock():
        pass


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_artisan():
    """
    Create a sample artisan in the database for testing.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Insert sample artisan
            cursor.execute(
                """
                INSERT INTO auth_user (username, first_name, last_name, email, password, is_staff, is_superuser)
                VALUES ('testartisan', 'John', 'Doe', 'testartisan@example.com', 'hashed_password', TRUE, FALSE)
                RETURNING id;
                """
            )
            artisan_id = cursor.fetchone()[0]
        conn.commit()
        return artisan_id
    finally:
        conn.close()


def test_delete_artisan_success(client, sample_artisan):
    """
    Test successful deletion of an artisan.
    """
    url = reverse('delete_artisan')  # Use the URL name defined in urls.py

    # Send POST request with artisan ID in body
    response = client.post(
        url,
        {"id": str(sample_artisan)},
        content_type="application/json"
    )

    # Assertions
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "Artisan deleted successfully."}


def test_delete_artisan_not_found(client):
    """
    Test deletion of a non-existing artisan.
    """
    url = reverse('delete_artisan')

    # Send POST request with non-existent ID
    response = client.post(
        url,
        {"id": "99999"},
        content_type="application/json"
    )

    # Assertions
    assert response.status_code == 404
    assert response.json() == {"success": False, "message": "Artisan not found."}


def test_delete_artisan_missing_id(client):
    """
    Test deletion with missing ID in the request body.
    """
    url = reverse('delete_artisan')

    # Send POST request without 'id' in body
    response = client.post(
        url,
        {},
        content_type="application/json"
    )

    # Assertions
    assert response.status_code == 400
    assert response.json() == {"success": False, "message": "Artisan ID is required."}


def test_delete_artisan_invalid_method(client):
    """
    Test invalid HTTP method (GET instead of POST).
    """
    url = reverse('delete_artisan')

    # Send GET request instead of POST
    response = client.get(url)

    # Assertions
    assert response.status_code == 405
    assert response.json() == {"success": False, "message": "Method not allowed."}
