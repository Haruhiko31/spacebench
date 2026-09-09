from .conftest import make_metadata, make_init_metadata, make_payload

def test_health_returns_200(client):
    response = client.get("/health")



def test_health_response_body(client):
    response = client.get("/health")

    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"

def test_analysis_returns_200(client):
    metadata = make_init_metadata()
    payload = make_payload(metadata=metadata)

    response = client.post("/pod/runs?tested=true", json=payload.model_dump())

    assert response.status_code == 200

def test_analysis_missing_payload(client):
    response = client.post("/pod/runs?tested=true")

    assert response.status_code == 422