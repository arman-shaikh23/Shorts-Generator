import pytest
from app.core.database import get_db

@pytest.mark.asyncio
async def test_database_connection(mock_db_lifecycle):
    # Example integration test to ensure DB object is available
    db = get_db()
    assert db is not None
