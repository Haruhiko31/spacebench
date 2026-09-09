from app.core.database import get_session, SessionLocal
from app.models import Run
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from ..enums import RunPhase, RunStatus, LogLevel
from ..services.run_logger import RunLogger
from ..schemas import RunRequest
from fastapi import APIRouter, BackgroundTasks, Depends
from starlette.responses import HTMLResponse
from datetime import datetime
import georinex as gr
import xarray
from scipy.interpolate import CubicSpline
import numpy as np
from app.estimators import get_estimator
from app.core.settings import settings

router = APIRouter(prefix="/pod/runs", tags=["Runs"])

import os

BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "backend")
C = 299792458  # speed of light

# ════════════ DEBUG MODE ══════════════════════════════════════════════════════════════════════════════════════════════

DEBUG_MODE = settings.DEBUG_MODE

# ════════════ HELPERS ═════════════════════════════════════════════════════════════════════════════════════════════════

# ═══ PARSE CLK FILE
def parse_clk(path):
    clocks = {}
    with open(path, "r") as f:
        for line in f:
            if line.startswith("AS "):
                parts = line.split()
                if DEBUG_MODE: print(parts)
                sat = parts[1]
                date = datetime(int(parts[2]), int(parts[3]), int(parts[4]), int(parts[5]), int(parts[6]),
                                int(float(parts[7])))
                bias = float(parts[9])

                # [IMPROVEMENT] Weight with clock sigma
                if sat not in clocks:
                    clocks[sat] = {}
                clocks[sat][date] = bias

    if DEBUG_MODE: print(clocks)

    return clocks


# ═══ INTERPOLATE GNSS SP3 PRECISE PRODUCT
''' This is required because RINEX has a time window from 10s where SP3 has 15' window.
    http://www.acc.igs.org/orbits/orbit-interp_gpssoln06.pdf 
'''


def interpolate_sp3(precise_product, rinex_epoch):
    # Step 1 : Convert both to float seconds
    sp3_times = precise_product.time.values
    t0 = sp3_times[0]
    sp3_seconds = (sp3_times - t0) / np.timedelta64(1, 's')
    target_seconds = (rinex_epoch - t0) / np.timedelta64(1, 's')

    interpolated = {}

    # We do that for every space vehicle (sat)
    for sv in precise_product.sv.values:
        x = precise_product.sel(sv=sv)['position'].values

        # remove NaN (count where not isNaN)
        mask = ~np.isnan(x[:, 0])

        # should be removed if there are not a least 4 points (for cubic polynomiale)
        if mask.sum() < 4:
            continue

        # build the spline
        cs = CubicSpline(sp3_seconds[mask], x[mask])
        interpolated[sv] = cs(target_seconds)

    return interpolated


''' This is required because RINEX has a time window from 10s where CLK has 30' window.
    Uses numpy Interpolation due to the Linearinity of clock biases
'''


def interpolate_clk(clock_corrections, rinex_epochs):
    interpolated = {}

    for sv in clock_corrections:

        # Get the time and bias
        times_and_biases = clock_corrections[sv]
        sorted_times = sorted(times_and_biases.keys())

        biases = []
        clk_epochs = []

        for time in sorted_times:
            biases.append(times_and_biases[time])
            clk_epochs.append(np.datetime64(time))

        biases = np.array(biases)
        clk_epochs = np.array(clk_epochs)

        # Converting to float seconds
        t0 = clk_epochs[0]
        clk_seconds = (clk_epochs - t0) / np.timedelta64(1, 's')
        target_seconds = (rinex_epochs - t0) / np.timedelta64(1, 's')

        # effective interpolation
        interpolated[sv] = np.interp(target_seconds, clk_seconds, biases)

    return interpolated


def get_initial_RSO_state(reference_truth, first_epoch_analysis):
    # get the midnight one (because of n-1 22:00 → n+1 00:00)
    try:
        pos = reference_truth["position"].sel(time=first_epoch_analysis).values
    except KeyError:
        raise ValueError(
            f"RSO does not contain the required first analysis epoch: {first_epoch_analysis}"
        )

    if DEBUG_MODE: print(f"First pos RSO : {pos}")

    if pos is None:
        raise ValueError(
            f"RSO position is missing at first analysis epoch: {first_epoch_analysis}"
        )

    #print(f"First pos RSO : {pos}")  # First pos RSO : [[-1219.129279 -3141.660387  5717.320582]]

    pos = pos[0]  # [[ → [

    pos = np.asarray(pos, dtype=float)

    # km → m
    pos_in_meter = pos * 1000

    initial_state = np.array([
        pos_in_meter[0],
        pos_in_meter[1],
        pos_in_meter[2],
        0.0
    ])

    if DEBUG_MODE: print(f"First analysis epoch: {first_epoch_analysis}")
    if DEBUG_MODE: print(f"Initial RSO state [m]: {initial_state}")

    return initial_state


# For epoch, get { [epoch] [ [SV] [{X,Y,Z}] [clock bias] }
def build_epoch_observations(observations, interp_sat_positions, sat_clocks, t):
    # Epoque (e.g. '2010 07 19 00:00:00')
    epoch = observations.time.values[t]

    ''' ════════ RINEX OBS ════════ '''
    # Pseudorange C1
    pseudorange = observations["C1"].sel(time=epoch).dropna("sv")

    # Sat
    visible_svs = pseudorange.sv.values

    # pseudorange value (in meters)
    pr_values = pseudorange.values

    epoch_obs = {}

    # we have a set of sv, separate each of them (e.g. G01,G02,G03,...)
    for i in range(len(visible_svs)):
        sv = str(visible_svs[i])

        # pseudorange for this sat
        P = pr_values[i]

        # Sat must exist in SP3 interpolation
        if sv not in interp_sat_positions:
            continue

        # Sat must exist in CLK interpolation
        if sv not in sat_clocks:
            continue

        sat_pos = interp_sat_positions[sv][t]  # {x,y,z}
        dt_sat = sat_clocks[sv][t]  # delta time

        # we should skip undefined value (pseudorange value)
        if np.isnan(P):
            continue

        # same for sat interp pos
        if np.any(np.isnan(sat_pos)):
            continue

        # same for clock
        if np.isnan(dt_sat):
            continue

        # Epoch → {
        #   "P" => pseudorange value for this sat at this epoch in METERS)          → OBS RNX
        #   "sat_pos" => precise value from IGS for this sat                        → IGS precise pos (km → m)
        #   "dt_sat" => clock bias for this sat at this epoch                 → clock bias
        # }
        epoch_obs[sv] = {
            "P": float(P),  # meters
            "sat_pos": np.asarray(sat_pos, dtype=float) * 1000,  # km → m
            "dt_sat": float(dt_sat)  # seconds
        }

    return epoch, epoch_obs
    # returns the values from an epoch ('2010-07-19 && {"P", "sat_pos", "dt_sat"})








# Get one RSO from a selected epoch
def get_rso_epoch_data(reference_truth, epoch):
    try:
        pos = reference_truth['position'].sel(time=epoch).values
    except KeyError:
        return None  # the epoch does not exist

    pos = np.asarray(pos, dtype=float).squeeze()  # [[ → [

    if pos.shape != (3,):
        #print(f"[RSO] Unexpected position shape at {epoch}: {pos.shape}, value={pos}")
        return None

    if np.any(np.isnan(pos)):
        return None

    return pos * 1000.0  # km → m

# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════════════






# ════ Phase 1 : Init and fetch the metadata from pre-validation ═══════════════════════════════════════════════════════

async def init(payload: RunRequest, logger: RunLogger):
    """ Log start, update run status """
    await logger.write_log('[POD ENGINE] Starting pod pipeline', RunPhase.init)
    await logger.write_log('[POD ENGINE] Getting all the data from backend validation', RunPhase.init)

    # Get the metadata from Backend Validation
    try:
        metadata = payload.metadata

        rso_sp3_starts = []
        for metad in payload.metadata["rso_sp3"]:
            rso_sp3_starts.append(metad["start_epoch"])

        results = {
            "rinex_start": metadata["rinex"]["start_epoch"],
            "gnss_clk_start": metadata["clk"]["first_as_timestamp"],
            "gnss_sp3_start": metadata["gnss_sp3"]["start_epoch"],
            "rso_sp3_start": rso_sp3_starts
        }

        if not all(results.values()):
            await logger.write_log('[POD ENGINE] Missing metadata fields', RunPhase.init, LogLevel.error)
            await logger.set_status(RunStatus.failed)
            return None

    except (KeyError, TypeError) as e:
        await logger.write_log(f'[POD ENGINE] Metadata extraction failed: {e}', RunPhase.init, LogLevel.error)
        await logger.set_status(RunStatus.failed)
        return None

    await logger.write_log('[POD ENGINE] Metadata fetched successfully', RunPhase.init)

    return results


# ════ Phase 2 : Cross-File Validation  ═════════════════════════════════════

async def cross_validate(metadata, logger: RunLogger):
    await logger.write_log('------------------------------------------------------', RunPhase.validation)
    await logger.write_log('[POD ENGINE] Starting Cross-File Validation', RunPhase.validation)

    rinex_start = metadata["rinex_start"]
    gnss_clk_start = metadata["gnss_clk_start"]
    gnss_sp3_start = metadata["gnss_sp3_start"]
    rso_sp3_starts = metadata["rso_sp3_start"]

    await logger.write_log(f'[POD ENGINE] Rinex start epoch : {rinex_start.replace("T", " ")}', RunPhase.validation)
    await logger.write_log(f'[POD ENGINE] GNSS CLOCK start epoch : {gnss_clk_start.replace("T", " ")}',
                           RunPhase.validation)
    await logger.write_log(f'[POD ENGINE] GNSS SP3 start epoch : {gnss_sp3_start.replace("T", " ")}',
                           RunPhase.validation)
    await logger.write_log(f'[POD ENGINE] RSO SP3 start epoch : {[s.replace("T", " ") for s in rso_sp3_starts]}',
                           RunPhase.validation)

    rinex_dt = datetime.fromisoformat(rinex_start)
    gnss_clk_dt = datetime.fromisoformat(gnss_clk_start)
    gnss_sp3_dt = datetime.fromisoformat(gnss_sp3_start)

    tolerance_second = 60

    # RINEX VS IGS SP3
    if abs((rinex_dt - gnss_sp3_dt).total_seconds()) > tolerance_second:
        await logger.write_log(f'[POD ENGINE] RINEX and IGS SP3 start epochs don\'t match', RunPhase.validation,
                               LogLevel.error)
        await logger.set_status(RunStatus.failed)
        return False

    # RINEX VS IGS CLK
    if abs((rinex_dt - gnss_clk_dt).total_seconds()) > tolerance_second:
        await logger.write_log(f'[POD ENGINE] RINEX and IGS CLK start epochs don\'t match', RunPhase.validation,
                               LogLevel.error)
        await logger.set_status(RunStatus.failed)
        return False

    # RINEX VS RSO files (note : the RSO is particular because it cover like day n-1 22:00 to day n+1 00:00:00
    rso_earliest = min(datetime.fromisoformat(s) for s in rso_sp3_starts)
    rso_latest = max(datetime.fromisoformat(s) for s in rso_sp3_starts)

    if rinex_dt < rso_earliest:
        await logger.write_log('[POD ENGINE] RSO coverage starts after RINEX', RunPhase.validation)
        await logger.set_status(RunStatus.failed)
        return False

    if rinex_dt > rso_latest:
        await logger.write_log('[POD ENGINE] RSO coverage ends before RINEX', RunPhase.validation)
        await logger.set_status(RunStatus.failed)
        return False

    # SP3 VS CLK
    if abs((gnss_sp3_dt - gnss_clk_dt).total_seconds()) > tolerance_second:
        await logger.write_log(f'[POD ENGINE] IGS SP3 and IGS CLK start epochs don\'t match', RunPhase.validation,
                               LogLevel.error)
        await logger.set_status(RunStatus.failed)
        return False

    # [IMPROVEMENT] Possible improvement, verify the satellite system compatibility

    await logger.write_log(f'[POD ENGINE] Cross Validation PASSED', RunPhase.validation, LogLevel.success)
    await logger.write_log('------------------------------------------------------', RunPhase.validation)
    return True  # Passed


# ════ Phase 3 : Parsing ════════════════════════════════════════════════════

async def parse(config, logger: RunLogger):
    await logger.write_log(f'[POD ENGINE] Starting parsing...', RunPhase.parsing, LogLevel.info)

    """ ═════════════  Parse RINEX obs → epochs + pseudoranges ═════════════ """  # this is Z in montenbruck (Z = (Z1, Z2, Z3 ... Zn))

    rinex_file = os.path.normpath(os.path.join(BACKEND_ROOT, config.rinex_path))
    if DEBUG_MODE: print(f"Rinex path => {rinex_file}")
    if DEBUG_MODE: print(f"Exists => {os.path.exists(rinex_file)}")
    if DEBUG_MODE: print(f"Size => {os.path.getsize(rinex_file) if os.path.exists(rinex_file) else 'N/A'}")

    rnx_obs = gr.load(rinex_file)

    first_epoch_data = rnx_obs['C1'].sel(time=rnx_obs.time[0]).dropna('sv')
    last_epoch_data = rnx_obs['C1'].sel(time=rnx_obs.time[-1]).dropna('sv')

    await logger.write_log(f'[POD ENGINE] RINEX loaded: {len(rnx_obs.time)} epochs, {len(rnx_obs.sv)} SVs',
                           RunPhase.parsing)
    await logger.write_log(
        f'[POD ENGINE] → First RINEX Epoch: {rnx_obs.time.values[0]} : {first_epoch_data.values} for vehicles {first_epoch_data.sv.values}',
        RunPhase.parsing)
    await logger.write_log(
        f'[POD ENGINE] → Last RINEX Epoch: {rnx_obs.time.values[-1]} : {last_epoch_data.values} for vehicles {last_epoch_data.sv.values}',
        RunPhase.parsing)

    """ ═════════════  Parse RSO SP3 → reference orbit ═════════════ """  # Use after the estimation to compare. (8.1.1)

    rso_paths = []
    rso_obs = []
    for rso_path in config.rso_sp3_paths:
        rso_paths.append(os.path.normpath(os.path.join(BACKEND_ROOT, rso_path)))

    for rso_path in rso_paths:
        if DEBUG_MODE: print(f"RSO paths => {rso_path}")
        if DEBUG_MODE: print(f"Exists => {os.path.exists(rso_path)}")
        if DEBUG_MODE: print(f"Size => {os.path.getsize(rso_path) if os.path.exists(rso_path) else 'N/A'}")
        rso_obs.append(gr.load(rso_path))

    # Combine
    rso_combined = xarray.concat(rso_obs, dim='time').sortby('time')

    await logger.write_log(f'[POD ENGINE] RSO loaded: {len(rso_combined.time)} positions', RunPhase.parsing)

    """ ═════════════  Parse GNSS SP3 → satellite positions ═════════════ """  # Used to get the h(x_0), if we know where the gnss sat is, and we guess where CHAMP is, the distance between those is the pseudorange H(x_0)

    gnss_sp3_path = os.path.normpath(os.path.join(BACKEND_ROOT, config.gnss_sp3_path))
    if DEBUG_MODE: print(f"GNSS SP3 path => {gnss_sp3_path}")
    if DEBUG_MODE: print(f"Exists => {os.path.exists(gnss_sp3_path)}")
    if DEBUG_MODE: print(f"Size => {os.path.getsize(gnss_sp3_path) if os.path.exists(gnss_sp3_path) else 'N/A'}")

    gnss_sp3_obs = gr.load(gnss_sp3_path)

    first_epoch_data = gnss_sp3_obs['position'].sel(time=gnss_sp3_obs.time[0]).dropna('sv')
    last_epoch_data = gnss_sp3_obs['position'].sel(time=gnss_sp3_obs.time[-1]).dropna('sv')

    await logger.write_log(f'[POD ENGINE] GNSS SP3 loaded: {len(gnss_sp3_obs.time)} epochs, {len(gnss_sp3_obs.sv)} SVs',
                           RunPhase.parsing)
    await logger.write_log(
        f'[POD ENGINE] → First GNSS SP3 Epoch: {gnss_sp3_obs.time.values[0]} : {first_epoch_data.values} for vehicles {first_epoch_data.sv.values}',
        RunPhase.parsing)
    await logger.write_log(
        f'[POD ENGINE] → Last GNSS SP3 Epoch: {gnss_sp3_obs.time.values[-1]} : {last_epoch_data.values} for vehicles {last_epoch_data.sv.values}',
        RunPhase.parsing)

    """ ═════════════  Parse CLK → clock corrections ═════════════ 6-12-13"""  # Because the satellites clock aren't perfect, enhanced atomic clocks are needed to correct. (clock bias x speed of light = meters of errors)

    gnss_clk_path = os.path.normpath(os.path.join(BACKEND_ROOT, config.gnss_clk_path))
    if DEBUG_MODE: print(f"CLK path => {gnss_clk_path}")
    if DEBUG_MODE: print(f"Exists => {os.path.exists(gnss_clk_path)}")
    if DEBUG_MODE: print(f"Size => {os.path.getsize(gnss_clk_path) if os.path.exists(gnss_clk_path) else 'N/A'}")
    gnss_clk_obs = parse_clk(gnss_clk_path)
    await logger.write_log(f'[POD ENGINE] CLK loaded: {len(gnss_clk_obs)} satellites', RunPhase.parsing)

    await logger.write_log(f'[POD ENGINE] Parsing PASSED', RunPhase.parsing, LogLevel.success)

    await logger.write_log('------------------------------------------------------', RunPhase.parsing, LogLevel.info)

    return {
        "observations": rnx_obs,
        "precise_product": gnss_sp3_obs,
        "clock_corrections": gnss_clk_obs,
        "reference_truth": rso_combined
    }


# ════ Phase 4 : Estimation ═════════════════════════════════════════════════
""" Interpolation, build equations, run estimator """


# Usage of 8.8 → 8.15 from Montenbruck as the core equations

# Jacobian Matrix : A rectangular matrix where we have more row than column (more obs than unknowns). It can defined as "how much a small change in input map to a change in output".
# Difference with KF : KF use {epoch ; epoch+1} because epochs aren't independants. In BLSQ and Kinematic, each epoch are independant so we should iterate over each epoch independantly.
# 1st step : Linearize the equation, because pseudorange equation is nonlinear. This is 8.8 in montenbruck → p as pseudorange. p = \delta{z} - H * \delta{x_0}.
# (1) get the visible pseudorange from obs, get the interpolated GPS satellite position, apply clock correction, then iterate over 8.17 (montenbruck)
#
# Interpolation : http://www.acc.igs.org/orbits/orbit-interp_gpssoln06.pdf -
#
# GNSS SP3 : /15'
# GNSS CLK : /30''
# RINEX    : /10''
#
async def estimate(payload, parsed_files, estimation_type: str, logger: RunLogger):
    await logger.write_log(f'[POD ENGINE] Starting Estimation...', RunPhase.estimation, LogLevel.info)
    await logger.write_log(f'[POD ENGINE] Estimation picked : {estimation_type}', RunPhase.estimation, LogLevel.info)


    results = {}

    # Initial RAW data
    observations = parsed_files["observations"]
    precise_prod = parsed_files["precise_product"]
    clock_corrections = parsed_files["clock_corrections"]
    reference_truth = parsed_files["reference_truth"]

    # First step, interpolate the /15' epoch from GNSS Precise product to /10'' RINEX
    obs_epoch = observations.time.values
    sat_precise_positions = interpolate_sp3(precise_prod, obs_epoch)

    await logger.write_log(
        f'[POD ENGINE] Interpolation precise_product → RINEX succeeded for {len(sat_precise_positions)} satellites',
        RunPhase.estimation)

    sat_clocks = interpolate_clk(clock_corrections, obs_epoch)

    await logger.write_log(
        f'[POD ENGINE] Interpolation clocks biases → RINEX succeeded for {len(sat_clocks)} satellites',
        RunPhase.estimation)

    await logger.write_log(f"[POD ENGINE] Estimation max_iter set to {payload.config.max_iteration}",
                           RunPhase.estimation, LogLevel.info)
    await logger.write_log(f"[POD ENGINE] Estimation tolerance set to {payload.config.tolerance}", RunPhase.estimation,
                           LogLevel.info)

    previous_state = None
    estimated_states = []
    position_errors = []
    iteration_stop = 0
    estimator_selector = get_estimator(payload.config.estimator_type)

    if payload.config.estimator_type == 'custom':
        plugin_path = os.path.normpath(os.path.join(BACKEND_ROOT, payload.config.estimator_path))
        estimator = estimator_selector(config=payload.config, logger=logger, plugin_path = plugin_path)
    else:
        estimator = estimator_selector(config=payload.config, logger=logger)

    # All the pseudorange from obs (C1 in the .RNX files)
    for t in range(len(observations.time)):
        epoch = observations.time[t]
        pseudoranges = observations['C1'].sel(time=epoch).dropna('sv')

        epoch, epoch_obs = build_epoch_observations(
            observations=observations,
            interp_sat_positions=sat_precise_positions,
            sat_clocks=sat_clocks,
            t=t
        )

        # We only use complete one ( SV, P, SAT_POS, BIAS )
        if len(epoch_obs) < 4:
            continue

        # Initial condition would be bad with 0,0,0,0 because real mission has initial condition (given by the first pos while separation).
        if estimator.previous_state is None:
            try:
                # get the first RSO obs
                initial_state = get_initial_RSO_state(reference_truth, epoch)  # r = (x,y,z) and clock bias
            except ValueError as e:
                # if RSO does not contain the initial state for {epoch}, set the analysis to FAILED.
                await logger.write_log(f"[POD ENGINE] {e}", RunPhase.estimation, LogLevel.error)
                await logger.set_status(RunStatus.failed)
                return False
        else:
            initial_state = estimator.previous_state.copy()

        estimated_state, diagnostics = estimator.estimate_epoch(epoch_obs, initial_state)

        estimator.previous_state = estimated_state.copy()

        iteration_stop = diagnostics.get('iterations_to_stop',0)
        convergence = diagnostics.get('corrections_history', [])

        if t % 1000 == 0:
            await logger.write_log(
                f'[POD ENGINE] Epoch {t} convergence: {[f"{c:.4f}" for c in convergence]}m',
                RunPhase.estimation
            )

        estimated_states.append({
            "epoch": epoch,
            "state": estimated_state,
            "satellite_count": len(epoch_obs)
        })

        if DEBUG_MODE:
            print(f"Epoch: {epoch}")
            print(f"Estimated position [m]: {estimated_state[0:3]}")
            print(f"Receiver clock bias [m]: {estimated_state[3]}")
            print(f"Receiver clock bias [s]: {estimated_state[3] / C}")

        # Finally we compare this with RSO (ground truth)

        rso_pos_m = get_rso_epoch_data(reference_truth, epoch)

        if rso_pos_m is not None:
            estimated_pos_m = estimated_state[0:3]

            error_vector = estimated_pos_m - rso_pos_m

            position_errors.append(error_vector)

            if DEBUG_MODE: print(f"RSO position [m]: {rso_pos_m}")
            if DEBUG_MODE: print(f"Error vector [m]: {error_vector}")

    # If there are pos errors
    if len(position_errors) > 0:
        position_errors = np.asarray(position_errors)  # ECEF [X,Y,Z]

        # https://gssc.esa.int/navipedia/index.php/Positioning_Error
        # np.sqrt(np.mean(np.sum(positions_errors **2)))
        rms_3d = np.sqrt(
            np.mean(
                position_errors[:, 0] ** 2 +
                position_errors[:, 1] ** 2 +
                position_errors[:, 2] ** 2
            )
        )

        print(f"ENDED with 3D RMS error [m]: {rms_3d}")

        results = {
            "rms_3d": rms_3d,
            "radial": None,
            "cross_track": None,
            "along_track": None
        }




    await logger.write_log(f'[POD ENGINE] Convergence set after {iteration_stop} iteration{ "s" if iteration_stop > 1 else "" }', RunPhase.estimation, LogLevel.success)
    await logger.write_log(f'[POD ENGINE] 3D RMS : {rms_3d}', RunPhase.estimation, LogLevel.success)
    await logger.write_log(f'[POD ENGINE] Estimation PASSED', RunPhase.estimation, LogLevel.success)
    await logger.write_log('------------------------------------------------------', RunPhase.estimation, LogLevel.info)
    return results


# ════ Phase 5 : Results ════════════════════════════════════════════════════
""" Compare vs reference, compute RMS and write to DB """


async def save_results(logger: RunLogger, run_id: int, results: list[int]):
    await logger.write_log('------------------------------------------------------', RunPhase.results)

    await logger.write_log(f'[POD ENGINE] Saving results...', RunPhase.results, LogLevel.info)

    # Save results ...

    async with SessionLocal() as session:
        run = await session.get(Run, run_id)

        if not run:
            await logger.write_log(f"[POD ENGINE] Run not found : {run_id}")
            return False

        run.rms_3d = results["rms_3d"] * 100  # m → cm
        run.radial = results["radial"]  # None
        run.along_track = results["along_track"]  # None
        run.cross_track = results["cross_track"]  # None

        await session.commit()

    await logger.write_log(f'[POD ENGINE] Saving results PASSED', RunPhase.results, LogLevel.success)

    await logger.write_log('------------------------------------------------------', RunPhase.results)

    return True


# ════ CORE POD ENGINE ════════════════════════════════════════════════════
async def run_pod_pipeline(payload: RunRequest):
    # LOGGER SERVICE
    LoggerService = RunLogger(payload.run_id)

    await LoggerService.write_log(
        f"[POD ENGINE] Run started — model: {payload.config.orbital_model}, estimator: {payload.config.estimator_type}",
        RunPhase.init, LogLevel.info)

    # ════ Phase 1 : Init ═══════════════════════════════════════════════════════
    metadata = await init(payload, LoggerService)
    if not metadata:
        await LoggerService.write_log(f'[POD ENGINE] Saving results FAILED', RunPhase.results, LogLevel.error)
        await LoggerService.set_status(RunStatus.failed)
        return

    # ════ Phase 2 : Cross-File Validation  ═════════════════════════════════════
    """ The aim is to validate if all the files cover the same time window """
    if not await cross_validate(metadata, LoggerService):
        await LoggerService.write_log(f'[POD ENGINE] Saving results FAILED', RunPhase.results, LogLevel.error)
        await LoggerService.set_status(RunStatus.failed)
        return

    # ════ Phase 3 : Parsing ════════════════════════════════════════════════════
    parsed = await parse(payload.config, LoggerService)
    if not parsed:
        await LoggerService.write_log(f'[POD ENGINE] Saving results FAILED', RunPhase.results, LogLevel.error)
        await LoggerService.set_status(RunStatus.failed)
        return

    # ════ Phase 4 : Estimation ═════════════════════════════════════════════════
    results = await estimate(payload, parsed, payload.config.estimator_type, LoggerService)
    if not results:
        await LoggerService.write_log(f'[POD ENGINE] Saving results FAILED', RunPhase.results, LogLevel.error)
        await LoggerService.set_status(RunStatus.failed)
        return

    # ════ Phase 5 : Results ════════════════════════════════════════════════════
    """ Compare vs reference, compute RMS and write to DB """

    await save_results(LoggerService, payload.run_id, results)

    await LoggerService.set_status(RunStatus.done)
    pass


@router.post("", response_class=HTMLResponse)
async def run_analysis(payload: RunRequest, background_tasks: BackgroundTasks,  tested = False):
    if DEBUG_MODE: print(f"Reaching the POD Engine correctly! With the payload : {payload}")

    # Pass if PyTest
    if not tested:
        background_tasks.add_task(run_pod_pipeline, payload)

    pass
