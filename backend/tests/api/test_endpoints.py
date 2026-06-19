def test_music_library_endpoint(client):
    # Example API test
    response = client.get("/api/v1/music-library")
    assert response.status_code == 200
    data = response.json()
    assert "library" in data
    assert isinstance(data["library"], list)


def test_pool_health_endpoint(client):
    response = client.get("/api/v1/health/pools")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "issues" in payload
    assert "http_pool" in payload
    assert "mongo_pool" in payload


def test_index_health_endpoint(client):
    response = client.get("/api/v1/health/indexes")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "collections" in payload
    assert "missing_total" in payload

    collections = payload["collections"]
    assert "users" in collections
    assert "refresh_tokens" in collections
    assert "projects" in collections
    assert "uploads" in collections
    assert "generated_shorts" in collections
    assert "idempotency_keys" in collections

    uploads = collections["uploads"]
    assert "expected_indexes" in uploads
    assert "actual_indexes" in uploads
    assert "missing_indexes" in uploads
