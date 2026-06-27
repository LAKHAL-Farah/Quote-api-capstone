from app.worker import generate_digest


# add near the top of tests/test_worker.py, before the test functions
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
import app.worker as worker_module

TEST_DATABASE_URL = "sqlite:///./test_worker.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

worker_module.SessionLocal = TestingSessionLocal  # point the worker's session at the test DB


@pytest.fixture(autouse=True)
def setup_and_teardown_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_generate_digest_task_is_registered():

    assert hasattr(generate_digest, "delay")


def test_generate_digest_runs_synchronously_when_called_directly():
    
    result = generate_digest.run(num_quotes=2)
    assert isinstance(result, list)