# Endpoint = /api/files
import os


# upload valid file
def test_upload_valid_file(uploaded_file):
    assert "id" in uploaded_file
    assert uploaded_file['original_name'] == 'test_file.sp3'

# Cannot upload an invalid ext file
def test_upload_bad_extension(client):
    response = client.post(
        "/api/files/upload",
        files={"file": ("test.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    # raise HTTPException(status_code=400, detail=f"Unsupported file type '{ext}'. Accepted: {accepted_extensions}")

# File content is not valid
def test_upload_invalid_content(client):
    test_path = os.path.join(os.path.dirname(__file__), "fixtures", "test_file_invalid.sp3")

    with open(test_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("test_file_invalid.sp3", f, "application/octet-stream")}
        )

    assert response.status_code == 422
    assert "File not valid" in response.json()["detail"]


# Download an existing file
def test_download_existing_file(client, uploaded_file):
    file_id = uploaded_file['id']
    response = client.get(f"/api/files/{file_id}/download")
    assert response.status_code == 200

# Download non existing file
def test_download_non_existing_file(client, uploaded_file):
    file_id = 'non_existing_file'
    response = client.get(f"/api/files/{file_id}/download")
    assert response.status_code == 404
    # raise HTTPException(status_code=404, detail="File not found")

# Bulk download
def test_bulk_download_existing(client, uploaded_file):
    response = client.post("/api/files/bulk/download", json=[uploaded_file["id"]])
    assert response.status_code == 200


# Bulk download invalid file
def test_bulk_download_non_existing(client, uploaded_file):
    response = client.post("/api/files/bulk/download", json=["non_existing_file"])
    assert response.status_code == 404
    # raise HTTPException(status_code=404, detail="File not found")

# Bulk download empty list
def test_bulk_download_empty(client, uploaded_file):
    response = client.post("/api/files/bulk/download", json=[])
    assert response.status_code == 400
    # raise HTTPException(status_code=400, detail="No files ID provided")

