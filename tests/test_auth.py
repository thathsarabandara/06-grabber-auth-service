from datetime import datetime, timedelta
from app.models.user import User, UserStatus
from app.models.email_verification import EmailVerification
from app.models.password_reset import PasswordReset
from app.models.session import Session as DbSession
from app.core.security import get_password_hash, get_otp_hash, get_reset_token_hash

def test_register_user_success(client, db):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "securepassword123",
            "phone": "+1234567890"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "john@example.com"
    assert data["first_name"] == "John"
    assert data["status"] == UserStatus.PENDING_VERIFICATION.value

    user = db.query(User).filter(User.email == "john@example.com").first()
    assert user is not None
    assert user.status == UserStatus.PENDING_VERIFICATION

    verification = db.query(EmailVerification).filter(EmailVerification.user_id == user.id).first()
    assert verification is not None
    assert verification.is_used is False


def test_register_user_duplicate_email(client, db):
    # Setup initial user
    user = User(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "password": "securepassword123"
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_verify_otp_success(client, db):
    # Setup pending user
    user = User(
        first_name="Alice",
        last_name="Smith",
        email="alice@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    otp = "123456"
    verification = EmailVerification(
        user_id=user.id,
        otp_hash=get_otp_hash(otp),
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(verification)
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "alice@example.com", "otp": otp}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully. Account is now active."

    db.refresh(user)
    assert user.status == UserStatus.ACTIVE
    db.refresh(verification)
    assert verification.is_used is True


def test_verify_otp_user_not_found(client):
    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "nonexistent@example.com", "otp": "123456"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_verify_otp_no_active_otp(client, db):
    user = User(
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "bob@example.com", "otp": "123456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "No active OTP found"


def test_verify_otp_expired(client, db):
    user = User(
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    verification = EmailVerification(
        user_id=user.id,
        otp_hash=get_otp_hash("123456"),
        expires_at=datetime.utcnow() - timedelta(minutes=1)
    )
    db.add(verification)
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "bob@example.com", "otp": "123456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "OTP expired"


def test_verify_otp_too_many_attempts(client, db):
    user = User(
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    verification = EmailVerification(
        user_id=user.id,
        otp_hash=get_otp_hash("123456"),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        attempts=3
    )
    db.add(verification)
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "bob@example.com", "otp": "123456"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Too many attempts. Request a new OTP."


def test_verify_otp_invalid(client, db):
    user = User(
        first_name="Bob",
        last_name="Smith",
        email="bob@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    verification = EmailVerification(
        user_id=user.id,
        otp_hash=get_otp_hash("123456"),
        expires_at=datetime.utcnow() + timedelta(minutes=15),
        attempts=1
    )
    db.add(verification)
    db.commit()

    response = client.post(
        "/api/v1/auth/verify-otp",
        json={"email": "bob@example.com", "otp": "000000"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid OTP"
    db.refresh(verification)
    assert verification.attempts == 2


def test_resend_otp_success(client, db):
    user = User(
        first_name="Charlie",
        last_name="Brown",
        email="charlie@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    old_verification = EmailVerification(
        user_id=user.id,
        otp_hash=get_otp_hash("111111"),
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(old_verification)
    db.commit()

    response = client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "charlie@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "OTP resent successfully"

    db.refresh(old_verification)
    assert old_verification.is_used is True

    new_verification = db.query(EmailVerification).filter(
        EmailVerification.user_id == user.id,
        EmailVerification.is_used == False
    ).first()
    assert new_verification is not None


def test_resend_otp_user_not_found(client):
    response = client.post(
        "/api/v1/auth/resend-otp",
        json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_login_success(client, db):
    user = User(
        first_name="Dave",
        last_name="Smith",
        email="dave@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "refresh_token" in response.cookies


def test_login_invalid_credentials(client, db):
    user = User(
        first_name="Dave",
        last_name="Smith",
        email="dave@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"


def test_login_inactive_user(client, db):
    user = User(
        first_name="Dave",
        last_name="Smith",
        email="dave@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.PENDING_VERIFICATION
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "password123"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Account is not active"


def test_logout(client, db):
    user = User(
        first_name="Eve",
        last_name="Jones",
        email="eve@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    refresh_token = "somerandomrefreshtoken1234567890"
    from app.core.security import get_refresh_token_hash
    session = DbSession(
        user_id=user.id,
        refresh_token_hash=get_refresh_token_hash(refresh_token),
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    db.add(session)
    db.commit()

    client.cookies.set("refresh_token", refresh_token)
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"
    assert "refresh_token" not in response.cookies or response.cookies.get("refresh_token") == ""

    db.refresh(session)
    assert session.is_revoked is True


def test_forgot_password_user_exists(client, db):
    user = User(
        first_name="Frank",
        last_name="Miller",
        email="frank@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "frank@example.com"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "If the email is registered, a password reset link has been sent."

    reset_entry = db.query(PasswordReset).filter(PasswordReset.user_id == user.id).first()
    assert reset_entry is not None
    assert reset_entry.is_used is False


def test_forgot_password_user_not_exists(client):
    response = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 200


def test_reset_password_success(client, db):
    user = User(
        first_name="Frank",
        last_name="Miller",
        email="frank@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    token = "mysecretresettoken12345"
    reset_entry = PasswordReset(
        user_id=user.id,
        reset_token_hash=get_reset_token_hash(token),
        expires_at=datetime.utcnow() + timedelta(minutes=15)
    )
    db.add(reset_entry)

    session = DbSession(
        user_id=user.id,
        refresh_token_hash="somehash",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    db.add(session)
    db.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newsecurepassword123"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Password reset successfully. Please login with your new password."

    db.refresh(user)
    from app.core.security import verify_password
    assert verify_password("newsecurepassword123", user.password_hash)

    db.refresh(reset_entry)
    assert reset_entry.is_used is True

    db.refresh(session)
    assert session.is_revoked is True


def test_reset_password_invalid_token(client):
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "invalidtoken", "new_password": "newsecurepassword123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"


def test_reset_password_expired_token(client, db):
    user = User(
        first_name="Frank",
        last_name="Miller",
        email="frank@example.com",
        password_hash=get_password_hash("password123"),
        status=UserStatus.ACTIVE
    )
    db.add(user)
    db.commit()

    token = "expiredtoken12345"
    reset_entry = PasswordReset(
        user_id=user.id,
        reset_token_hash=get_reset_token_hash(token),
        expires_at=datetime.utcnow() - timedelta(minutes=1)
    )
    db.add(reset_entry)
    db.commit()

    response = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "new_password": "newsecurepassword123"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid or expired reset token"
