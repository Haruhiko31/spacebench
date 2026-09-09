import asyncio

import pytest
from core.database import SessionLocal
from fastapi.testclient import TestClient
from app.main import app
import os

from app.models.pod import Run, RunLog, RunRsoFile
from sqlalchemy import delete


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as client:
        yield client


# VALID FILE
@pytest.fixture(scope="session")
def uploaded_file(client) -> dict:

    test_path = os.path.join(os.path.dirname(__file__), "fixtures", "test_file.sp3")

    with open(test_path, "rb") as f:
        response = client.post(
            "/api/files/upload",
            files={"file": ("test_file.sp3", f, "application/octet-stream")}
        )

    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="session")
def created_run(client, uploaded_file) -> dict:
    response = client.post("/api/runs", json={
        "name": "TEST_RUN",
        "orbital_model": "kinematic",
        "estimator_type": "BLSQ",
        "mission_name": "TEST_MISSION",
        "mission_year": 2010,
        "mission_day": 200,
        "rinex_file_id": uploaded_file["id"],
        "gnss_sp3_file_id": uploaded_file["id"],
        "gnss_clk_file_id": uploaded_file["id"],
        "rso_file_ids": [],
    })
    assert response.status_code == 201
    return response.json()

@pytest.fixture(scope="session", autouse=True)
def cleanup(created_run):
    yield

    async def clean():
        async with SessionLocal() as session:
            run_id = created_run['id']

            await session.execute(delete(RunLog).where(RunLog.run_id == run_id))
            await session.execute(delete(RunRsoFile).where(RunRsoFile.run_id == run_id))

            run = await session.get(Run, run_id)
            if run:
                await session.delete(run)

            await session.commit()

    asyncio.get_event_loop().run_until_complete(clean())
