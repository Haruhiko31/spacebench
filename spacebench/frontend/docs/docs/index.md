# Welcome to SpaceBench

**SpaceBench** is an open-source benchmark platform for **Precise Orbit Determination (LEO-POD)**, released under the [MIT License](https://opensource.org/licenses/MIT) and developed as a Master's thesis at the Université de Namur.

It lets researchers and engineers upload geodetic input files, configure an orbital model and estimator, launch a full POD pipeline run, and compare the accuracy of results through an interactive dashboard.

---

## What is Precise Orbit Determination?

Precise Orbit Determination (POD) is the process of computing the trajectory of a Low Earth Orbit (LEO) satellite with centimetre-level accuracy, using onboard GPS observations combined with precise satellite orbit and clock products from the International GNSS Service (IGS).

SpaceBench focuses on the **undifferenced (zero-difference)** approach: a single-receiver technique where the LEO receiver clock is estimated epoch-by-epoch, and GPS satellite clocks are corrected using IGS CLK_30S records.

---

## What SpaceBench does

| Step | Description |
|------|-------------|
| **Upload** | Accepts 4 input files: onboard RINEX observations, RSO reference orbit, IGS precise orbits, and IGS clock corrections |
| **Configure** | Choose the kinematic orbital model and an estimator for the MVP: least squares or a custom Python plugin |
| **Run** | Launches the POD pipeline as an asynchronous background job with phase-by-phase logs |
| **Compare** | Displays RMS results (3D, Radial, Along-track, Cross-track) in a sortable table and histogram |

---

## Mission compatibility

SpaceBench is mission-agnostic. Any LEO satellite that provides onboard RINEX 2 observations and an RSO SP3 reference orbit can be used, paired with IGS SP3 and CLK_30S products from any compatible source.

The dashboard comes pre-populated with placeholder runs for demonstration purposes. Real input files are provided for the **CHAMP** mission:

| Day | Date |
|-----|------|
| D200 | 2010-07-19 |
| D201-D219 | 2010-07-20 to 2010-08-07 |
| D246 | 2010-09-03 |
