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
