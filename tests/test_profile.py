import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch
from app.models.user import User, UserStatus
from app.models.session import Session as DbSession
from app.core.security import get_password_hash, create_access_token, verify_password

@pytest.fixture
def active_user(db):
    user = User(
        first_name="Profile",
        last_name="User",
        email="profile@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def auth_headers(active_user):
    token = create_access_token(active_user.id)
    return {"Authorization": f"Bearer {token}"}

def test_get_profile_success(client, active_user, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == active_user.email
    assert data["first_name"] == active_user.first_name
    assert data["status"] == UserStatus.ACTIVE.value

def test_get_profile_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_get_profile_invalid_token(client, db):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

    token = create_access_token("nonexistent-uuid")
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

def test_update_profile_success(client, active_user, auth_headers, db):
    response = client.patch(
        "/api/v1/auth/me",
        json={
            "first_name": "UpdatedName",
            "last_name": "UpdatedLast",
            "phone": "+9876543210"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "UpdatedName"
    assert data["last_name"] == "UpdatedLast"
    assert data["phone"] == "+9876543210"

    db.refresh(active_user)
    assert active_user.first_name == "UpdatedName"
    assert active_user.phone == "+9876543210"

@patch("app.api.routes.profile.os.path.exists")
@patch("app.api.routes.profile.os.remove")
@patch("app.api.routes.profile.aiofiles.open")
def test_upload_profile_image_success_and_overwrite(
    mock_aio_open, mock_os_remove, mock_os_exists, client, active_user, auth_headers, db
):
    import io
    mock_file = MagicMock()
    mock_file.write = AsyncMock()
    
    mock_aio_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
    mock_aio_open.return_value.__aexit__ = AsyncMock(return_value=None)
    
    mock_os_exists.return_value = True
    file1 = io.BytesIO(b"fake image content 1")
    response = client.post(
        "/api/v1/auth/me/image",
        files={"file": ("avatar1.png", file1, "image/png")},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    img_path_1 = data["profile_image"]
    assert img_path_1.startswith("/uploads/profile_images/")
    
    mock_aio_open.assert_called_once()
    mock_file.write.assert_called_once()
    
    mock_aio_open.reset_mock()
    mock_file.write.reset_mock()

    db.refresh(active_user)
    assert active_user.profile_image == img_path_1

    file2 = io.BytesIO(b"fake image content 2")
    response = client.post(
        "/api/v1/auth/me/image",
        files={"file": ("avatar2.jpg", file2, "image/jpeg")},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    img_path_2 = data["profile_image"]
    assert img_path_2.startswith("/uploads/profile_images/")
    assert img_path_2 != img_path_1

    assert mock_os_remove.call_count == 1
    mock_aio_open.assert_called_once()
    mock_file.write.assert_called_once()

def test_upload_profile_image_invalid_type(client, auth_headers):
    import io
    file_data = io.BytesIO(b"some plain text data")
    response = client.post(
        "/api/v1/auth/me/image",
        files={"file": ("test.txt", file_data, "text/plain")},
        headers=auth_headers
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "File provided is not an image"

def test_change_password_success(client, active_user, auth_headers, db):
    session = DbSession(
        user_id=active_user.id,
        refresh_token_hash="somehash",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    db.add(session)
    db.commit()

    response = client.post(
        "/api/v1/auth/me/change-password",
        json={
            "old_password": "password123",
            "new_password": "newsupersecurepassword123"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password changed successfully"

    db.refresh(active_user)
    assert verify_password("newsupersecurepassword123", active_user.password_hash)

    db.refresh(session)
    assert session.is_revoked is True

def test_change_password_invalid_old(client, active_user, auth_headers, db):
    response = client.post(
        "/api/v1/auth/me/change-password",
        json={
            "old_password": "wrongpassword",
            "new_password": "newsupersecurepassword123"
        },
        headers=auth_headers
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid previous password"
