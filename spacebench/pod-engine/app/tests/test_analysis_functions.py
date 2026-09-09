import pytest
from app.estimators import LSQEstimator
from .conftest import make_metadata, make_init_metadata, make_payload
from app.routers import init, cross_validate, parse_clk, interpolate_clk, interpolate_sp3, get_rso_epoch_data, get_initial_RSO_state
from datetime import datetime
import os
import numpy as np
import xarray as xr
import georinex as gr
from app.estimators import get_estimator

# ══════════ HELPERS ═════════════════════════════════════════════════════════

def get_clk_file():
    return os.path.join(os.path.dirname(__file__), "fixtures", "test.clk_30s")

def load_rso():
    rso_path = ""
    rso_obs = []

    rso_path = os.path.join(os.path.dirname(__file__), "fixtures", "test_rso_d200.sp3")
    rso_obs.append(gr.load(rso_path))

    # Combine
    rso_combined = xr.concat(rso_obs, dim='time').sortby('time')

    return rso_combined

# ══════════ Phase 1 - INIT ═══════════════════════════════════════

@pytest.mark.asyncio
async def test_init_passes(logger):
    metadata = make_init_metadata()
    payload = make_payload(metadata=metadata)
    result = await init(payload, logger)
    assert result is not None
    assert "rinex_start" in result

@pytest.mark.asyncio
async def test_init_not_all(logger):
    metadata = make_init_metadata(gnss_clk=None)
    payload = make_payload(metadata=metadata)
    result = await init(payload, logger)
    assert result is None

@pytest.mark.asyncio
async def test_init_missing_dict_key(logger):
    metadata = make_init_metadata(gnss_clk=None)
    del metadata['rinex']
    payload = make_payload(metadata=metadata)
    result = await init(payload, logger)
    assert result is None


# ══════════ Phase 2 - CROSS_VALIDATE ═══════════════════════════════════════

@pytest.mark.asyncio
async def test_cross_validate_passes(logger):
    metadata = make_metadata()
    result = await cross_validate(metadata, logger)
    assert result is True

@pytest.mark.asyncio
async def test_cross_validate_small_offset_sp3_ok(logger):
    metadata = make_metadata(gnss_sp3="2010-07-20T00:00:30")
    result = await cross_validate(metadata, logger)
    assert result is True

@pytest.mark.asyncio
async def test_cross_validate_small_offset_clk_ok(logger):
    metadata = make_metadata(gnss_clk="2010-07-20T00:00:30")
    result = await cross_validate(metadata, logger)
    assert result is True

@pytest.mark.asyncio
async def test_cross_validate_small_offset_sp3_60s_ok(logger):
    metadata = make_metadata(gnss_sp3="2010-07-20T00:01:00")
    result = await cross_validate(metadata, logger)
    assert result is True

@pytest.mark.asyncio
async def test_cross_validate_small_offset_clk_60s_ok(logger):
    metadata = make_metadata(gnss_clk="2010-07-20T00:01:00")
    result = await cross_validate(metadata, logger)
    assert result is True

@pytest.mark.asyncio
async def test_cross_validate_small_offset_sp3_nok(logger):
    metadata = make_metadata(gnss_sp3="2010-07-20T00:01:01")
    result = await cross_validate(metadata, logger)
    assert result is False

@pytest.mark.asyncio
async def test_cross_validate_small_offset_clk_nok(logger):
    metadata = make_metadata(gnss_clk="2010-07-20T00:01:01")
    result = await cross_validate(metadata, logger)
    assert result is False

@pytest.mark.asyncio
async def test_cross_validate_rso_earliest_one_arc_ok(logger):
    metadata = make_metadata(rso_starts=["2010-07-20T00:00:00"])
    result = await cross_validate(metadata, logger)
    assert result is True

@pytest.mark.asyncio
async def test_cross_validate_rso_earliest_nok(logger):
    metadata = make_metadata(rso_starts=["2010-07-21T22:00:00","2010-07-21T00:00:00"])
    result = await cross_validate(metadata, logger)
    assert result is False

@pytest.mark.asyncio
async def test_cross_validate_rso_latest_nok(logger):
    metadata = make_metadata(rso_starts=["2010-07-19T22:00:00","2010-07-17T00:00:00"])
    result = await cross_validate(metadata, logger)
    assert result is False

@pytest.mark.asyncio
async def test_cross_validate_diff_clk_sp3_nok(logger):
    metadata = make_metadata(gnss_sp3="2010-07-20T00:00:00", gnss_clk="2010-07-20T00:01:01")
    result = await cross_validate(metadata, logger)
    assert result is False

# ══════════ Phase 3 - PARSING ═══════════════════════════════════════

# ══════ Parse_clk

def test_parse_clk_reads_sats():
    path = get_clk_file()
    result = parse_clk(path)

    assert "G01" in result
    assert "G02" in result
    assert len(result) == 2

def test_parse_clk_correct_bias():
    path = get_clk_file()
    result = parse_clk(path)
    epoch = datetime(2010, 7, 20, 0, 0, 0)
    epoch2 = datetime(2010, 7, 20, 0, 0, 30)
    epoch3 = datetime(2010, 7, 20, 0, 0, 0)
    #print(result["G01"][epoch])
    #print(result["G01"][epoch2])
    #print(result["G02"][epoch3])
    assert result["G01"][epoch] == 0.000123456789
    assert result["G01"][epoch2] == 0.000234567890
    assert result["G02"][epoch3] == -0.000050000000

def test_parse_clk_skip_AR():
    path = get_clk_file()
    result = parse_clk(path)
    assert "IGS1" not in result

# ══════ interpolate_clk
def test_interpolate_clk_mid():
    clock_corrections = {
        "G01": {
            datetime(2010, 7, 20, 0, 0, 0): 1.0,
            datetime(2010, 7, 20, 0, 0, 30): 2.0,
        }
    }

    target = np.array([np.datetime64("2010-07-20T00:00:15")])
    result = interpolate_clk(clock_corrections, target)

    assert "G01" in result
    assert result["G01"][0] == 1.5

def test_interpolate_clk_known_epoch():
    clock_corrections = {
        "G01": {
            datetime(2010, 7, 20, 0, 0, 0): 1.0,
            datetime(2010, 7, 20, 0, 0, 30): 2.0,
        }
    }

    target = np.array([np.datetime64("2010-07-20T00:00:00")])
    result = interpolate_clk(clock_corrections, target)

    assert "G01" in result
    assert result["G01"][0] == 1.0

# ══════ interpolate_sp3

def test_interpolate_sp3_skips_missing_sv_value():
    times = np.array([
        np.datetime64("2010-07-20T00:00:00"),
        np.datetime64("2010-07-20T00:15:00"),
        np.datetime64("2010-07-20T00:30:00"),
    ])  # missing 4th value (mask.sum)

    position = np.array([[[1, 2, 3]], [[4, 5, 6]], [[7, 8, 9]]], dtype=float)

    ds = xr.Dataset(
        {"position": (["time", "sv", "ECEF"], position)},
        coords={"time": times, "sv": ["G01"]},
    )

    target = np.array([np.datetime64("2010-07-20T00:07:30")])
    result = interpolate_sp3(ds, target)

    assert "G01" not in result  # skipped due to < 4 values

# ══════════ Phase 4 - ESTIMATE ═══════════════════════════════════════

def test_get_existing_estimator():
    assert get_estimator("BLSQ") is LSQEstimator

def test_get_non_existing_estimator():
    with pytest.raises(ValueError):
        get_estimator("Non existing estimator")

def test_get_rso_epoch_data_passed():
    rso = load_rso()
    first_epoch = rso.time.values[0]

    result = get_rso_epoch_data(rso, first_epoch)

    np.testing.assert_allclose(result, [-1219129.279, -3141660.387, 5717320.582])

def test_get_rso_epoch_data_unknown():
    rso = load_rso()
    non_existing_epoch = np.datetime64("1400-01-01T00:00:00")

    result = get_rso_epoch_data(rso, non_existing_epoch)

    assert result is None


def test_initial_rso_state_passed():
    rso = load_rso()
    first_epoch = rso.time.values[0]

    result = get_initial_RSO_state(rso, first_epoch)

    assert result.shape == (4,)
    np.testing.assert_allclose(result, [-1219129.279, -3141660.387, 5717320.582, 0.0])
    assert result[3] == 0.0

def test_initial_rso_state_missing_epoch():
    rso = load_rso()

    with pytest.raises(ValueError):
        get_initial_RSO_state(rso, np.datetime64("1400-01-01T00:00:00"))

