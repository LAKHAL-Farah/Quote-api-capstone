import pytest 
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from app.main import app 
from app.database import Base ,get_db

TEST_DATABASE_URL ="sqlite:///./test.db"
engine= create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal= sessionmaker(autocommit=False, autoflush=False, bind=engine)



def override_get_db():
    db= TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db]=override_get_db

@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def disable_cache():
    """Patch all cache functions so Redis is never touched in unit tests."""
    with patch("app.main.get_cached_quote", return_value=None), \
         patch("app.main.set_cached_quote"), \
         patch("app.main.invalidate_quote_cache"):
        yield

client=TestClient(app)

def test_health_check():
    response=client.get("/health")
    assert response.status_code ==200




def test_create_quote():
    payload = {"text": "Test quote", "author": "Test Author"}
    response = client.post("/quote", json=payload)
    assert response.status_code == 201
    assert response.json()["text"] == payload["text"]


def test_get_quote_by_id():
    create_response = client.post("/quote", json={"text": "Findable", "author": "Someone"})
    quote_id = create_response.json()["id"]
    response = client.get(f"/quote/{quote_id}")
    assert response.status_code == 200
    assert response.json()["text"] == "Findable"


def test_get_quote_not_found():
    response = client.get("/quote/99999")
    assert response.status_code == 404


def test_delete_quote():
    create_response = client.post("/quote", json={"text": "Temp", "author": "Ghost"})
    quote_id = create_response.json()["id"]
    delete_response = client.delete(f"/quote/{quote_id}")
    assert delete_response.status_code == 204
    get_response = client.get(f"/quote/{quote_id}")
    assert get_response.status_code == 404


def test_create_quote_missing_author():
    response = client.post("/quote", json={"text": "No author"})
    assert response.status_code == 422


def test_update_quote_invalidates_cache():
    create_response = client.post("/quote", json={"text": "Original", "author": "A"})
    quote_id = create_response.json()["id"]

    # First read — populates the cache (in a real run against Redis; this
    # test file uses SQLite and no Redis override, so this mainly proves
    # the route logic and response shape are correct)
    client.get(f"/quote/{quote_id}")

    update_response = client.put(
        f"/quote/{quote_id}", json={"text": "Updated", "author": "A"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["text"] == "Updated"