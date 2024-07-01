import pytest

from fastapi import status

from src.database.models import User

from unittest.mock import MagicMock


@pytest.fixture(scope="module")
def test_contact():
    return {"first_name": "John", "last_name": "Doe", "email": "john.doe@example.com", "phone_number": "1234567890", "birth_date": "1990-01-01"}


@pytest.fixture(scope="module")
def test_contact_update():
    return {"first_name": "Jane", "last_name": "Doe", "email": "jane.doe@example.com", "phone_number": "0987654321", "birth_date": "1991-02-02"}


@pytest.fixture()
def token(client, user, session, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.users.send_email", mock_send_email)
    client.post("/api/auth/signup", json=user)
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )

    data = response.json()
    return data["access_token"]


def test_create_contact(client, token, test_contact):
    response = client.post(
        "/api/contacts/create", 
        json=test_contact, 
        headers={"Authorization": f"Bearer {token}"},
        )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["first_name"] == test_contact["first_name"]
    assert data["last_name"] == test_contact["last_name"]
    assert data["email"] == test_contact["email"]
    assert "id" in data


def test_create_contact_duplicate_email(client, token, test_contact):
    response = client.post(
        "/api/contacts/create", 
        json=test_contact, 
        headers={"Authorization": f"Bearer {token}"},
        )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Contact with this email already exists."


def test_search_contacts(client, token, test_contact):
    response = client.get(f"/api/contacts/search?first_name={test_contact['first_name']}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert data[0]["first_name"] == test_contact["first_name"]


def test_get_upcoming_birthdays(client, token):
    response = client.get("/api/contacts/birthdays", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)