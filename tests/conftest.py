import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app

# In-memory SQLite test database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def auth_headers(client):
    """Registers and authenticates a test user, returning Bearer auth headers."""
    user_payload = {
        "name": "Test User",
        "email": "test.user@example.com",
        "password": "Password123!"
    }
    res = client.post("/api/auth/register", json=user_payload)
    if res.status_code == 201:
        token = res.json()["access_token"]
    else:
        login_res = client.post("/api/auth/login", json={
            "email": "test.user@example.com",
            "password": "Password123!"
        })
        token = login_res.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}
