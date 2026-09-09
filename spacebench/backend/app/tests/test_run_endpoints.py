# Endpoint = /api/run

''' ════════════ CREATE ════════════  '''

# Create a valid run
def test_run_valid(client, created_run):
    assert "id" in created_run
    assert created_run["name"] == "TEST_RUN"
    assert created_run["status"] == "pending"

# Create an invalid run
def test_run_invalid(client):
    response = client.post("/api/runs", json={
        "name": "TEST_RUN",
        "orbital_model": "kinematic",
        "estimator_type": "least_squares"
    })
    assert response.status_code == 422

''' ════════════ RUN COUNT  ════════════  '''

# Get run count
def test_get_run_count(client):
    response = client.get("/api/runs/count")
    assert response.status_code == 200
    assert response.json()['count'] >= 0

# Count runs filtered by status
def test_get_run_count_filtered_by_statut(client):
    response = client.get("/api/runs/count?statuses=pending")
    assert response.status_code == 200
    assert response.json()['count'] >= 0

# Count run filtered by an unknown status
def test_get_run_filtered_by_unknown_status(client):
    response = client.get("/api/runs/count?statuses=unknown_status")
    assert response.status_code == 422

''' ════════════ RUN GETTER ════════════  '''

# Get all runs
def test_get_list_runs(client):
    response = client.get("/api/runs")
    assert response.status_code == 200
    assert len(response.json()) >= 1

# Get an existing run
def test_get_existing_run(client, created_run):
    response = client.get(f"/api/runs/{created_run['id']}")
    assert response.status_code == 200
    assert response.json()['name'] == "TEST_RUN"

# Get a non-existing run
def test_get_non_existing_run(client):
    response = client.get("/api/runs/9999999")
    assert response.status_code == 404

# Get all run sorted
def test_list_runs_with_sort(client):
    response = client.get("/api/runs?sort_by=name&sort_order=asc&limit=5")
    assert response.status_code == 200

# List run filtered by status
def test_list_runs_filtered_by_status(client):
    response = client.get("/api/runs?statuses=pending")

    assert response.status_code == 200
    runs = response.json()
    assert len(runs) >= 1

# List run filtered by unknown status
def test_list_runs_filtered_by_unknown_status(client):
    response = client.get("/api/runs?statuses=unknown_status")

    assert response.status_code == 422


''' ════════════ RUN LOG GETTER  ════════════  '''

# Get run log
def test_get_run_logs(client, created_run):
    response = client.get(f"/api/runs/{created_run['id']}/logs")
    assert response.status_code == 200

# Get run logs from non existing run
def test_get_run_logs_non_existing(client):
    response = client.get('/api/runs/9999999/logs')
    assert response.status_code == 404



