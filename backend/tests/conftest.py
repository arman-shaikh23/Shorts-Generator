import pytest
import pytest_asyncio
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fastapi.testclient import TestClient
from main import app
from app.core.database import connect_to_mongo, close_mongo_connection

@pytest.fixture
def client():
    # Provide a TestClient to be used in API tests
    with TestClient(app) as client:
        yield client

@pytest_asyncio.fixture(autouse=True)
async def mock_db_lifecycle():
    # Setup and teardown for async tests that need DB access
    await connect_to_mongo()
    yield
    await close_mongo_connection()
