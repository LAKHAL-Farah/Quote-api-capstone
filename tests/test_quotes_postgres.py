import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

POSTGRES_TEST_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://testuser:testpass@localhost:5432/testdb"
)

engine = create_engine(POSTGRES_TEST_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check_against_real_postgres():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_create_and_retrieve_quote_against_real_postgres():
    payload = {"text": "Postgres-specific test", "author": "CI Runner"}
    create_response = client.post("/quote", json=payload)
    assert create_response.status_code == 201
    quote_id = create_response.json()["id"]

    get_response = client.get(f"/quote/{quote_id}")
    assert get_response.status_code == 200
    assert get_response.json()["text"] == payload["text"]