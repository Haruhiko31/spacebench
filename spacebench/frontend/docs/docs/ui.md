# User Interface

This page walks through the SpaceBench interface screen by screen.

---

## Login

![Login Page](assets/images/login.svg)

Default credentials can be found → here ←

---

## Dashboard

The dashboard is the main view after login. It centralises all POD processing data, featuring a filterable paginated table and a histogram for graphical visualisation.

![Dashboard](assets/images/dashboard-en.svg)

It is possible to show only one of the two components, or to widen the view using the "Wide View", "Table" and "Histogram" buttons.

![Dashboard](assets/images/dashboard-view.svg)

### Table

Displays all POD runs in a paginated table. Columns can be shown or hidden, data can be exported as CSV, columns can be sorted ascending or descending, and the logs for any run can be viewed.

![Dashboard](assets/images/dashboard-show-datatable-large.svg)

Clicking the **log icon** on a row opens the log viewer for that run.

![Log Viewer](assets/images/run-log.svg)

It is also possible to compare results with another analysis by clicking the **Compare** button at the bottom left.

![Log Viewer](assets/images/run-log-compare.svg)

### Histogram

The **histogram** at the bottom of the page shows RMS results across all runs. Results can be displayed as 3D RMS, Radial, Along-track, or Cross-Track. It is also possible to choose which runs are shown, their count, and their order.

Click a bar in the histogram to display a horizontal reference line.

![Dashboard](assets/images/dashboard-show-histogramme-large.svg)

---

## New Analysis — 4-step wizard

### Step 1 — Upload files

*Upload* the 4 required input files:

| File | Format | Source |
|------|--------|--------|
| RINEX observations | `.rnx` | Mission provider, e.g. GFZ / ISDC for CHAMP |
| IGS SP3 precise orbits | `.sp3` | IGS / CDDIS |
| IGS CLK_30S clock corrections | `.clk_30s` | IGS / CDDIS |
| RSO SP3 reference orbit | `.sp3` | Mission provider, e.g. GFZ / ISDC for CHAMP |

![Step 1 - Upload](assets/images/step-1.svg)

!!! note
    Demo data for CHAMP days 200 to 219 and day 246 can be loaded automatically via the **Demo Mission** button.

Each uploaded file is pre-validated automatically. If a file is invalid, it will be highlighted in red with an error message. A full list of pre-validation errors can be found in the [Error List](../error-list/).

![Step 1 - Upload Error](assets/images/step-1-error.svg)

!!! info "Built-in documentation"
    Documentation is available directly from the frontend via the **Documentation** button. Users can find pre-validation error codes (also available in the [Error List](../error-list/)) as well as a detailed breakdown of each supported file format (`.rnx`, `.sp3`, `.clk_30s`).

![Documentation - File formats](assets/images/file-format-doc.svg)

![Documentation - File detail](assets/images/file-format-file.svg)

### Step 2 — Orbital model

Only **Kinematic** is available. Dynamic and Reduced-Dynamic are not implemented.

![Step 2 - Orbital Model](assets/images/step-2.svg)

### Step 3 — Estimator

- **Least Squares** — current target estimator - The documentation is accessible here : []
- **Kalman filter** — not implemented and outside the MVP scope
- **Extended Kalman filter** — not implemented and outside the MVP scope
- **Unscented Kalman filter** — not implemented and outside the MVP scope
- **Custom plugin** — *upload* a `.py` file implementing the `BaseEstimator` interface

![Step 3 - Estimator](assets/images/step-3.svg)

The user can also configure the **maximum number of iterations** and the **convergence threshold** (tolerance). These parameters control the estimator's stopping criterion: the algorithm stops when the position correction falls below the tolerance, or when the maximum number of iterations is reached.

!!! tip "Custom Estimator"
    It is possible to extend the program's functionality by importing a custom estimator. Your `.py` file must contain a class extending `BaseEstimator` and implement the `estimate_epoch` method. Click the **Documentation** button to view the interface contract. A template is available to download via the button **download example**.

![Custom Estimator Interface](assets/images/custom-estimator.svg)

The estimator file is also pre-validated upon upload. See the [Error List](../error-list) for details.

### Step 4 — Name and launch

Review the run summary before launching.

![Step 4 - Recap](assets/images/step-4.svg)

Give the run a name and confirm. The pipeline starts immediately in the background.

![Mission Launched](assets/images/mission-launched.svg)

---

## Navigation bar

The navigation bar provides access to the documentation (MkDocs, Swagger, ReDoc), unit testing, or logout.

![Header](assets/images/header.svg)

## Unit testing

Runs the platform's unit tests and displays the results.

![Unit Testing](assets/images/unit-testing.svg)

The list of unit tests can be found in the [unit test page](../unit-test/).
