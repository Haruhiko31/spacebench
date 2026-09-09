# POD Engine

The POD Engine is the computation core of SpaceBench. When a run is submitted, the backend launches the engine as an asynchronous job. The engine receives already uploaded files, validation metadata, and the run configuration, then executes the scientific POD pipeline.

---

## 1. Input Files

The pipeline requires mission observation data, precise GNSS products, and a reference orbit.

### From the mission (e.g. GFZ / ISDC for CHAMP)

**RINEX 2 observations** (`.rnx`)

Onboard GPS receiver observations recorded by the LEO satellite. The CHAMP test files contain pseudorange, carrier phase, and Doppler observations. In the current POD implementation, the useful observable is:

| Observable | Meaning | Unit |
|------------|---------|------|
| `C1` | GPS C/A-code pseudorange | meters |

![RINEX 2 file format](assets/images/RINEX 2.svg)

The RINEX file is parsed with `georinex` and becomes an `xarray.Dataset`. For the CHAMP test data, the observation cadence is approximately 10 seconds.

**RSO SP3 - Reference Standard Orbit** (`.sp3`)

The RSO SP3 files provide the reference trajectory of the LEO satellite. They are not used to form the GNSS observation equations. They are used after estimation to compare the computed CHAMP trajectory with the reference orbit.

![SP3 file format](assets/images/SP3.svg)

For CHAMP, the reference satellite identifier is `L06`. The RSO files contain ECEF positions in kilometers and may contain velocities depending on the SP3 mode. Two overlapping arcs can be used for one observation day.

!!! note "Overlapping RSO arcs"
    When two SP3 RSO arcs are concatenated, overlapping epochs produce duplicate entries. The `get_rso_epoch_data()` function handles this case by ignoring epochs with an unexpected shape, so no comparison is performed for those epochs.

### From IGS / CDDIS

**IGS SP3 - precise GPS orbits** (`.sp3`)

The IGS SP3 file provides precise GPS satellite positions, usually at 15-minute intervals. These positions are needed to compute the geometric range between each GPS satellite and the unknown CHAMP receiver position.

The current implementation parses this file with `georinex` and interpolates each GPS satellite trajectory to the RINEX observation epochs.

**IGS CLK_30S - precise GPS clocks** (`.clk_30s`)

The CLK file provides precise GPS satellite clock biases at 30-second intervals. The current implementation parses `AS` records with a custom parser:

```python
clock_corrections[sv][datetime] = bias_seconds
```

![CLK 30S file format](assets/images/CLK 30S.svg)

!!! warning "Why CLK_30S is mandatory"
    In the pseudorange observation equation, the satellite clock term is multiplied by the speed of light and directly affects the modeled range. For this reason, SpaceBench uses the dedicated CLK_30S product instead of relying only on the clock values embedded in the 15-minute SP3 orbit file. This follows the standard GNSS observation modeling described by Montenbruck & Gill.

---

## 2. Data Received By The Engine

Before the engine starts, the backend has already uploaded and pre-validated each file. The engine receives two important objects:

| Object | Content |
|--------|---------|
| `config` | file ids, stored paths, orbital model, estimator type, estimator path (if custom), max iterations, tolerance |
| `metadata` | validation metadata extracted by the backend validators |

The metadata currently used by the engine is:

| Metadata field | Source file | Used in |
|----------------|-------------|---------|
| `rinex.start_epoch` | RINEX observation file | init, cross-file validation |
| `gnss_sp3.start_epoch` | IGS SP3 orbit file | init, cross-file validation |
| `clk.first_as_timestamp` | IGS CLK file | init, cross-file validation |
| `rso_sp3[*].start_epoch` | RSO SP3 reference files | init, cross-file validation |

This is not the same as scientific parsing. Pre-validation extracts lightweight metadata and catches malformed files early. The POD engine still parses the scientific content during the parsing phase.

---

## 3. Orbital Models

The orbital model defines how the LEO trajectory is parameterised during estimation.

| Model | Principle | Current role |
|-------|-----------|--------------|
| Kinematic | Estimate an independent position at every epoch | **Implemented** |
| Dynamic | Estimate an orbit constrained by equations of motion | Not implemented, outside MVP |
| Reduced-dynamic | Combine dynamics with empirical parameters | Not implemented, outside MVP |

The current implementation focuses on the kinematic model because it is the shortest complete path to a working POD result: each epoch can be solved independently from the pseudorange observations available at that epoch.

---

## 4. Estimators

The estimator solves the observation equations and produces the estimated trajectory.

### Estimator registry

Available estimators are registered in a central registry and resolved by name at runtime:

```python
REGISTRY: dict[str, type[BaseEstimator]] = {
    "BLSQ": LSQEstimator,
    "KF":   KFEstimator,
    "UKF":  UKFEstimator,
    "EKF":  EKFEstimator,
    "custom": CustomEstimator
}
```

| Estimator | Class | Status |
|-----------|-------|--------|
| Batch Least Squares | `LSQEstimator` | **Implemented** |
| Kalman Filter | `KFEstimator` | Not implemented, outside MVP |
| Extended Kalman Filter | `EKFEstimator` | Not implemented, outside MVP |
| Unscented Kalman Filter | `UKFEstimator` | Not implemented, outside MVP |
| Custom plugin | `CustomEstimator` | **Implemented** (dynamic loading) |

All estimators extend `BaseEstimator`, which defines the interface:

```python
class BaseEstimator(ABC):
    def __init__(self, config, logger: RunLogger):
        self.config = config
        self.logger = logger
        self.previous_state: np.ndarray | None = None

    @abstractmethod
    def estimate_epoch(self, epoch_obs: dict, initial_state: np.ndarray) -> tuple[np.ndarray, dict]:
        pass
```

### Least Squares Estimator (BLSQ)

The current target estimator is an epoch-by-epoch least-squares solver using the pseudorange model from Montenbruck & Gill, Chapter 8.

The estimated state for one epoch is:

```text
x = [X, Y, Z, dtr]
```

| Unknown | Meaning | Unit used internally |
|---------|---------|----------------------|
| `X, Y, Z` | CHAMP receiver ECEF position | meters |
| `dtr` | receiver clock range bias | meters |

At least four valid GPS satellites are required at an epoch because there are four unknowns.

The algorithm iterates until the position correction norm falls below the configured tolerance, or the maximum number of iterations is reached. At each iteration:

1. Compute the geometric range `ρ` between the current receiver position estimate and each satellite;
2. Compute the modeled pseudorange: `P_computed = ρ + dtr - c · dt_sat`;
3. Form the residual: `P_observed - P_computed`;
4. Build the Jacobian row: `[dx/ρ, dy/ρ, dz/ρ, 1.0]`;
5. Solve the overdetermined system with `numpy.linalg.lstsq`;
6. Apply the correction to the state vector.

The convergence criterion is:

```python
position_correction_norm = sqrt(dx² + dy² + dz²) < tolerance
```

### Custom Estimator Plugin

Users can upload a `.py` file implementing `BaseEstimator`. The `CustomEstimator` class uses `importlib` to dynamically load the uploaded file at runtime:

1. Load the Python module from the file path using `importlib.util`;
2. Auto-discover the first class that extends `BaseEstimator`;
3. Instantiate it with the same `config` and `logger`;
4. Delegate all `estimate_epoch` calls to the loaded plugin.

This allows users to experiment with their own estimation algorithms without modifying the SpaceBench codebase.

### Observation equation

The pseudorange observation equation used in the least-squares estimator follows the Code Based Positioning model:

```text
R^j = ρ^j + c(δt_rcv - δt^j_sat) + ε^j
```

| Symbol | Meaning | Source |
|--------|---------|--------|
| `R^j` | Observed pseudorange for satellite j | RINEX `C1` |
| `ρ^j` | Geometric range `sqrt(dx² + dy² + dz²)` | Computed from state and IGS SP3 |
| `c` | Speed of light (299,792,458 m/s) | Constant |
| `δt_rcv` | Receiver clock bias | Estimated (4th unknown) |
| `δt^j_sat` | Satellite clock bias | IGS CLK_30S |
| `ε^j` | Measurement noise / residual | Implicit |

The following error sources are not modeled in the current MVP:

| Source | Symbol | Reason |
|--------|--------|--------|
| Tropospheric delay | `T^j` | LEO altitude (~400 km) is above the troposphere |
| Ionospheric delay | `α·I^j` | Requires dual-frequency observations |
| Satellite group delay | `TGD^j` | Second-order effect |
| Multipath | `M^j` | Environment-dependent |

---

## 5. Scientific Pipeline

The engine pipeline is implemented as independent functions:

```text
run_pod_pipeline()
  -> init()
  -> cross_validate()
  -> parse()
  -> estimate()
  -> save_results()
```

Each phase writes logs through `RunLogger`. These logs are stored in the database and displayed in the frontend log console.

### Pipeline phases

| Phase | Function | Description | Status |
|-------|----------|-------------|--------|
| **1 - Init** | `init()` | Load run metadata produced by backend validation | **Implemented** |
| **2 - Cross-file validation** | `cross_validate()` | Check that selected files cover a coherent time window | **Implemented** |
| **3 - Parse files** | `parse()` | Load RINEX, GNSS SP3, CLK, and RSO data | **Implemented** |
| **4 - Estimation** | `estimate()` | Interpolate products and solve kinematic least squares | **Implemented** |
| **5 - Results** | `save_results()` | Compare against RSO and persist RMS metrics | **Implemented** |

---

## Phase 1 - Init

The init phase starts the run and extracts the metadata needed before parsing.

Current extracted values:

| Value | Meaning |
|-------|---------|
| `rinex_start` | observation start epoch from RINEX metadata |
| `gnss_clk_start` | first `AS` timestamp from CLK metadata |
| `gnss_sp3_start` | IGS SP3 start epoch |
| `rso_sp3_start` | list of RSO SP3 start epochs |

If a required metadata field is missing, the run is marked as `failed`.

---

## Phase 2 - Cross-File Validation

This phase checks whether the selected files are compatible with each other.

Current checks:

| Check | Rule |
|-------|------|
| RINEX vs IGS SP3 | start epochs must match within 60 seconds |
| RINEX vs IGS CLK | start epochs must match within 60 seconds |
| IGS SP3 vs IGS CLK | start epochs must match within 60 seconds |
| RINEX vs RSO SP3 arcs | RSO coverage must include the RINEX start epoch |

The RSO files are handled differently from the IGS products because reference orbit arcs can overlap the observation day. For CHAMP, the uploaded RSO set may contain two arcs around the target day.

Possible future checks outside the MVP:

| Check | Reason |
|-------|--------|
| Full RINEX time-window coverage | Prevent interpolation gaps later in the pipeline |
| Satellite constellation compatibility | Current data is GPS-only |
| Minimum usable satellites per epoch | Least squares needs at least four observations |

---

## Phase 3 - Parse Files

The parsing phase loads the scientific content using the `georinex` python library.

### RINEX observations

```python
rnx_obs = gr.load(rinex_file)
```

The important data variable is:

```python
observations["C1"]
```

For each epoch, missing pseudoranges are dropped:

```python
pseudoranges = observations["C1"].sel(time=epoch).dropna("sv")
```

### RSO reference orbit

Each RSO SP3 file is loaded with `georinex`, then the arcs are concatenated:

```python
rso_combined = xarray.concat(rso_obs, dim="time").sortby("time")
```

This produces the reference truth used during the result phase.

!!! warning "Overlapping arcs"
    When two RSO arcs overlap in time, duplicate epochs will have shape `(2, 3)` instead of `(3,)`. The `get_rso_epoch_data()` function handles this by skipping epochs with unexpected shapes, so no comparison is performed for those epochs.

### IGS SP3 precise orbits

The GNSS SP3 file is loaded with `georinex`:

```python
gnss_sp3_obs = gr.load(gnss_sp3_path)
```

The important data variable is:

```python
precise_product["position"]
```

Positions are provided in kilometers by the SP3 format and must be converted to meters before computing ranges against RINEX pseudoranges.

### IGS CLK precise clocks

The CLK file is parsed by `parse_clk()`, which keeps only satellite clock records:

```text
AS Gxx yyyy mm dd hh mm ss.sssss bias_seconds
```

The output is:

```python
{
    "G01": {
        datetime(...): bias_seconds,
        ...
    },
    ...
}
```

### Parsed outputs

The `parse()` function returns:

| Key | Type | Description |
|-----|------|-------------|
| `observations` | `xarray.Dataset` | RINEX observations, including `C1` pseudoranges |
| `precise_product` | `xarray.Dataset` | IGS GPS satellite positions |
| `clock_corrections` | `dict` | CLK satellite clock biases |
| `reference_truth` | `xarray.Dataset` | concatenated and deduplicated RSO reference trajectory |

---

## Phase 4 - Estimation

The estimation phase performs interpolation, builds epoch observations, and runs the selected estimator.

### Interpolation

The observation, orbit, and clock products do not share the same cadence:

| Data | Cadence | Interpolation method |
|------|---------|----------------------|
| RINEX `C1` observations | ~10 seconds | target epochs |
| IGS SP3 satellite positions | 15 minutes | cubic spline (`scipy.interpolate.CubicSpline`) |
| IGS CLK satellite clocks | 30 seconds | linear interpolation (`numpy.interp`) |

SP3 interpolation:

```python
cs = CubicSpline(sp3_seconds[mask], x[mask])
interpolated[sv] = cs(target_seconds)
```

Satellites with fewer than 4 valid data points are skipped (cubic spline requires at least 4 points).

CLK interpolation:

```python
interpolated[sv] = np.interp(target_seconds, clk_seconds, biases)
```

### Building epoch observations

For each RINEX epoch, the function `build_epoch_observations()` assembles the data needed by the estimator:

| Field | Source | Unit |
|-------|--------|------|
| `P` | RINEX `C1` pseudorange | meters |
| `sat_pos` | Interpolated IGS SP3 position (km → m) | meters |
| `dt_sat` | Interpolated IGS CLK bias | seconds |

Satellites are filtered out if any of the following is missing or `NaN`: pseudorange, interpolated position, or clock bias. If fewer than 4 valid satellites remain, the epoch is skipped.

### Initial state

The initial receiver state for the first epoch is derived from the RSO reference orbit:

```python
initial_state = [x_m, y_m, z_m, 0.0]  # position in meters + zero clock bias
```

For subsequent epochs, the previous estimated state is used as the initial guess, enabling faster convergence.

### Estimation loop

```text
for each RINEX epoch:
    1. build epoch observations (P, sat_pos, dt_sat)
    2. skip if < 4 valid satellites
    3. set initial state (RSO for first epoch, previous estimate otherwise)
    4. call estimator.estimate_epoch(epoch_obs, initial_state)
    5. store estimated state
    6. compare with RSO reference (if available) → compute error vector
```

---

## Phase 5 - Results

The results phase compares estimated positions against the RSO reference trajectory and persists the metrics.

### 3D RMS

The 3D RMS error is computed in the ECEF frame:

```python
rms_3d = sqrt(mean(ΔX² + ΔY² + ΔZ²))
```

where `ΔX, ΔY, ΔZ` are the position error components at each epoch.

The result is stored in the database in **centimeters**.

### Current metrics

| Metric | Status |
|--------|--------|
| RMS 3D | **Implemented** |
| RMS radial | Not implemented |
| RMS along-track | Not implemented |
| RMS cross-track | Not implemented |

### RTN frame (future)

The RTN (Radial, Transverse, Normal) frame is built from the reference orbit:

| Axis | Definition |
|------|------------|
| `R` | radial direction, normalized reference position |
| `T` | transverse direction, `N × R` |
| `N` | normal direction, normalized angular momentum |

If velocity is available in the RSO SP3 file, it can be used to compute the angular momentum. Otherwise, the velocity can be approximated with finite differences between neighboring reference positions.

!!! info "RTN decomposition"
    The RTN (Radial, Transverse, Normal) error decomposition is not implemented and is outside the scope of this project. Only the 3D RMS in the ECEF frame is computed.
---

## 6. Debug Mode

A global `DEBUG_MODE` flag can be toggled in `app/core/settings.py`:

```python
DEBUG_MODE: bool = True
```

When enabled, additional information is printed to the console during execution, including file paths, parsed values, estimated positions, and error vectors. This is useful for development and troubleshooting but should be disabled in production or during presentations.

---

## 7. Run Statuses

| Status | Meaning |
|--------|---------|
| `pending` | Run created, pipeline not yet started |
| `running` | Pipeline in progress |
| `done` | Pipeline completed successfully, RMS results available |
| `failed` | Pipeline encountered an unrecoverable error |

---

## 8. Implementation Summary

### Implemented

1. Metadata extraction from backend validation
2. Cross-file temporal validation (60-second tolerance)
3. RINEX, SP3, CLK, and RSO parsing with `georinex`
4. RSO arc concatenation and deduplication
5. SP3 cubic spline interpolation to observation epochs
6. CLK linear interpolation to observation epochs
7. Visible-satellite extraction and filtering per epoch
8. Unit conversion from SP3 kilometers to meters
9. Satellite clock correction in the observation equation
10. Jacobian matrix and residual vector construction
11. Iterative least-squares solution (`numpy.linalg.lstsq`)
12. Configurable max iterations and convergence tolerance
13. Estimated trajectory storage per epoch
14. RSO comparison and 3D RMS computation
15. Database persistence of results
16. Estimator registry with runtime resolution
17. Custom estimator plugin system via `importlib`
18. Phase-based logging through `RunLogger`
19. Debug mode toggle

### Not implemented (outside MVP)

1. RTN (Radial, Transverse, Normal) frame decomposition
2. Dynamic and reduced-dynamic orbital models
3. Kalman Filter, Extended Kalman Filter, Unscented Kalman Filter estimators
4. Tropospheric, ionospheric, and multipath error corrections
5. Satellite group delay (TGD) correction
6. Full time-window coverage validation
7. Multi-constellation support (currently GPS-only)