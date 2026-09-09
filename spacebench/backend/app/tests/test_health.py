def test_health_returns_200(client):
    response = client.get("/health")

    assert response.status_code == 200


def test_health_response_body(client):
    response = client.get("/health")

    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"

def test_redoc_returns_200(client):
    response = client.get("/api/redoc")
    assert response.status_code == 200

def test_swagger_returns_200(client):
    response = client.get("/api/docs")
    assert response.status_code == 200