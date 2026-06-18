def test_music_library_endpoint(client):
    # Example API test
    response = client.get("/api/v1/music-library")
    assert response.status_code == 200
    data = response.json()
    assert "library" in data
    assert isinstance(data["library"], list)
