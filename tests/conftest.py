import os
import pytest
from unittest.mock import AsyncMock, patch
from app.main import app  # noqa: E402
from app.core.database import Base, engine, SessionLocal  # noqa: E402
from app.api.deps import get_db  # noqa: E402
os.environ["DATABASE_URL"] = "sqlite:///./test_temp.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    # Remove the test database file
    db_file = "test_temp.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except Exception:
            pass

@pytest.fixture(name="db")
def db_fixture():
    connection = engine.connect()
    transaction = connection.begin()
    db = SessionLocal(bind=connection)
    
    yield db
    
    db.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(name="client")
def client_fixture(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(autouse=True)
def mock_fastmail():
    with patch("app.services.email_service.fast_mail.send_message", new_callable=AsyncMock) as mock_send:
        yield mock_send
