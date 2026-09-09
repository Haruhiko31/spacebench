import pytest
from fastapi.testclient import TestClient
from app.main import app
import os
from unittest.mock import AsyncMock, MagicMock
from app.schemas import RunRequest



from app.services.run_logger import RunLogger


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as client:
        yield client

# Logger
@pytest.fixture()
def logger():
    logger = MagicMock()
    logger.write_log = AsyncMock()
    logger.set_status = AsyncMock()
    return logger

# ═══════════ HELPERS ══════════════════════════════════════════════════

def make_metadata(
        rinex="2010-07-20T00:00:00",
        gnss_sp3="2010-07-20T00:00:00",
        gnss_clk="2010-07-20T00:00:00",
        rso_starts=None
):
    if rso_starts is None:
        rso_starts = ["2010-07-19T22:00:00","2010-07-20T23:59:59"]

    return {
        "rinex_start": rinex,
        "gnss_sp3_start": gnss_sp3,
        "gnss_clk_start": gnss_clk,
        "rso_sp3_start": rso_starts,
    }

def make_init_metadata(
        rinex="2010-07-20T00:00:00",
        gnss_sp3="2010-07-20T00:00:00",
        gnss_clk="2010-07-20T00:00:00",
        rso_starts=None
):
    if rso_starts is None:
        rso_starts = ["2010-07-19T22:00:00", "2010-07-20T23:59:59"]

    return {
        "rinex": {"start_epoch": rinex},
        "clk": {"first_as_timestamp": gnss_clk},
        "gnss_sp3": {"start_epoch": gnss_sp3},
        "rso_sp3": [{"start_epoch": s} for s in rso_starts],
    }

def make_payload(
        run_id = "1",
        config = None,
        metadata = None
):
    if metadata is None:
        metadata = make_metadata()

    if config is None:
        config = {
            "rinex_file_id": "test",
            "gnss_sp3_file_id": "test",
            "gnss_clk_file_id": "test",
            "rso_file_ids": [],
            "rinex_path": "",
            "gnss_sp3_path": "",
            "gnss_clk_path": "",
            "rso_sp3_paths": [],
            "orbital_model": "kinematic",
            "estimator_type": "BLSQ",
            "max_iteration": 10,
            "tolerance": 0.0001,
        }

    return RunRequest(
        run_id=run_id,
        config=config,
        metadata=metadata,
    )