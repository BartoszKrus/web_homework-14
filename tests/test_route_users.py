from unittest.mock import MagicMock

from src.database.models import User

import pytest


def test_create_user(client, user, monkeypatch):
    mock_send_email = MagicMock()
    monkeypatch.setattr("src.routes.users.send_email", mock_send_email)

    response = client.post(
        "/api/auth/signup", 
        json=user,
        )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user"]["email"] == user.get("email")
    assert data["user"]["username"] == user["username"]
    assert "id" in data["user"]


def test_repeat_create_user(client, user):
    response = client.post(
        "/api/auth/signup", 
        json=user,
        )

    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Account already exists"


def test_login_user_not_confirmed(client, user):
    response = client.post(
        "/api/auth/login", 
        data={"username": user.get('email'), "password": user.get('password')},
        )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Email not confirmed"


def test_login_user(client, session, user):
    current_user: User = session.query(User).filter(User.email == user.get('email')).first()
    current_user.confirmed = True
    session.commit()

    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": user.get('password')},
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user.get('email'), "password": 'wrong_password'},
    )

    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


def test_login_wrong_email(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": 'wrong_email', "password": user.get('password')},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.fixture(scope="module")
def access_token(client, user):
    response = client.post(
        "/api/auth/login",
        data={"username": user["email"], "password": user["password"]},
    )

    return response.json()["access_token"]


def test_get_user_me(client, access_token):
    response = client.get(
        "/api/auth/me/", 
        headers={"Authorization": f"Bearer {access_token}"},
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "username" in data
    assert "email" in data


def test_get_user_me_without_token(client):
    response = client.get(
        "/api/auth/me",
        )
    
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Not authenticated"