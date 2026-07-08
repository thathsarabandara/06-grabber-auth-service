import pytest
from unittest.mock import AsyncMock, patch
from app.services.email_service import EmailService
from app.api.deps import get_db

@pytest.mark.anyio
async def test_email_service_success():
    with patch("app.services.email_service.fast_mail.send_message", new_callable=AsyncMock) as mock_send:
        await EmailService.send_otp_email("test@example.com", "123456")
        mock_send.assert_called_once()
        
        mock_send.reset_mock()
        await EmailService.send_welcome_email("test@example.com")
        mock_send.assert_called_once()

        mock_send.reset_mock()
        await EmailService.send_password_reset_email("test@example.com", "http://localhost")
        mock_send.assert_called_once()

        mock_send.reset_mock()
        await EmailService.send_password_reset_success_email("test@example.com")
        mock_send.assert_called_once()

        mock_send.reset_mock()
        await EmailService.send_login_attempt_email("test@example.com", "now", "127.0.0.1", "Chrome")
        mock_send.assert_called_once()

@pytest.mark.anyio
async def test_email_service_failure():
    with patch("app.services.email_service.fast_mail.send_message", side_effect=Exception("SMTP error")) as mock_send:
        await EmailService.send_otp_email("test@example.com", "123456")
        await EmailService.send_welcome_email("test@example.com")
        await EmailService.send_password_reset_email("test@example.com", "http://localhost")
        await EmailService.send_password_reset_success_email("test@example.com")
        await EmailService.send_login_attempt_email("test@example.com", "now", "127.0.0.1", "Chrome")
        assert mock_send.call_count == 5

def test_get_db_generator():
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    try:
        next(db_gen)
    except StopIteration:
        pass

def test_create_access_token_with_delta():
    from datetime import timedelta
    from app.core.security import create_access_token
    token = create_access_token("some_subject", expires_delta=timedelta(minutes=10))
    assert token is not None

def test_get_current_user_no_sub(client):
    from jose import jwt
    from app.core.config import settings
    token = jwt.encode({"other": "claim"}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"

