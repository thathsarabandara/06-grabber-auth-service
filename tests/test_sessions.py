import pytest
from datetime import datetime, timedelta
from app.models.user import User, UserStatus
from app.models.session import Session as DbSession
from app.core.security import get_password_hash, create_access_token, get_refresh_token_hash

@pytest.fixture
def active_user(db):
    user = User(
        first_name="Session",
        last_name="User",
        email="sessions@example.com",
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

def test_get_sessions(client, active_user, auth_headers, db):
    session1 = DbSession(
        user_id=active_user.id,
        refresh_token_hash="hash1",
        device_info="Device 1",
        ip_address="192.168.1.1",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    session2 = DbSession(
        user_id=active_user.id,
        refresh_token_hash="hash2",
        device_info="Device 2",
        ip_address="192.168.1.2",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    session3 = DbSession(
        user_id=active_user.id,
        refresh_token_hash="hash3",
        device_info="Device 3",
        ip_address="192.168.1.3",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=True
    )
    db.add_all([session1, session2, session3])
    db.commit()

    response = client.get("/api/v1/auth/sessions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    
    ids = [s["id"] for s in data]
    assert session1.id in ids
    assert session2.id in ids
    assert session3.id not in ids

def test_revoke_session_success(client, active_user, auth_headers, db):
    session = DbSession(
        user_id=active_user.id,
        refresh_token_hash="hash1",
        device_info="Device 1",
        ip_address="192.168.1.1",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    db.add(session)
    db.commit()

    response = client.delete(f"/api/v1/auth/sessions/{session.id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Session revoked successfully"

    db.refresh(session)
    assert session.is_revoked is True

def test_revoke_session_not_found(client, auth_headers):
    response = client.delete("/api/v1/auth/sessions/nonexistent-session-id", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"

def test_revoke_session_unauthorized(client, active_user, auth_headers, db):
    other_user = User(
        first_name="Other",
        last_name="User",
        email="other@example.com",
        password_hash="somehash",
        status=UserStatus.ACTIVE
    )
    db.add(other_user)
    db.commit()

    session = DbSession(
        user_id=other_user.id,
        refresh_token_hash="hashother",
        device_info="Other Device",
        ip_address="1.1.1.1",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    db.add(session)
    db.commit()

    response = client.delete(f"/api/v1/auth/sessions/{session.id}", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"

def test_revoke_all_sessions_success(client, active_user, auth_headers, db):
    current_token = "currentrefresh12345"
    current_hash = get_refresh_token_hash(current_token)

    current_session = DbSession(
        user_id=active_user.id,
        refresh_token_hash=current_hash,
        device_info="Current Device",
        ip_address="192.168.1.1",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    other_session1 = DbSession(
        user_id=active_user.id,
        refresh_token_hash="otherhash1",
        device_info="Other Device 1",
        ip_address="192.168.1.2",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    other_session2 = DbSession(
        user_id=active_user.id,
        refresh_token_hash="otherhash2",
        device_info="Other Device 2",
        ip_address="192.168.1.3",
        expires_at=datetime.utcnow() + timedelta(days=7),
        is_revoked=False
    )
    
    db.add_all([current_session, other_session1, other_session2])
    db.commit()

    client.cookies.set("refresh_token", current_token)
    
    response = client.post("/api/v1/auth/sessions/revoke-all", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Revoked 2 other sessions"

    db.refresh(current_session)
    db.refresh(other_session1)
    db.refresh(other_session2)

    assert current_session.is_revoked is False
    assert other_session1.is_revoked is True
    assert other_session2.is_revoked is True
