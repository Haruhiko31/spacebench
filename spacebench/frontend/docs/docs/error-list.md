# Validation Error List

This page documents the error codes returned by the SpaceBench file validation system.

Each error contains:

| Field | Description |
|------|-------------|
| `code` | Stable error identifier |
| `message` | Human-readable error description |
| `line` | Line concerned in the file, when available. `0` means the error is global or not localized. |

---

## Common errors

These errors can appear for every supported file type.

| Code | File(s) | Cause | Recommended action |
|---|---|---|---|
| `FILE_EMPTY` | All | The file is empty. | Check that the selected file contains data. |
| `COMMON_FILE_DECODE_ERROR` | All | The file cannot be decoded. SP3, RINEX and CLK files are expected to be ASCII; Python plugins are expected to be UTF-8. | Check the file encoding or regenerate the file from its original source. |

---

## SP3 errors

These errors concern `.sp3` files, used for precise GNSS orbits or RSO reference orbits.

| Code | Cause | Recommended action |
|---|---|---|
| `SP3_FILE_TOO_SHORT` | The file contains too few lines to be a valid SP3 file. | Check that the SP3 file is not truncated. |
| `SP3_FILE_HEADER_ERROR` | The first SP3 header line is incomplete or malformed. | Check the first line of the file, for example `#dP...` or `#dV...`. |
| `SP3_FILE_VERSION_ERROR` | The SP3 version is not recognized. Accepted versions are `#a`, `#b`, `#c`, `#d`. | Provide a compatible SP3 file. |
| `SP3_FILE_MODE_ERROR` | The SP3 mode is invalid or the content does not match the declared mode. | Check the `P` or `V` mode character in the first line, and the `P` and `V` data records. |
| `SP3_FILE_START_EPOCH_ERROR` | The start epoch declared in the header cannot be parsed. | Check the date/time fields in the first SP3 header line. |
| `SP3_FILE_EPOCH_COUNT_ERROR` | The epoch count is missing, invalid, or zero. | Check the epoch count field in the SP3 header. |
| `SP3_FILE_NUMBER_OF_SATS_ERROR` | No satellite was found in the `+` header lines. | Check that the satellite list is present in the SP3 header. |
| `SP3_FILE_FIRST_EPOCH_ERROR` | No valid first epoch was found. | Check that an epoch line starting with `*` is present. |
| `SP3_FILE_DATA_ERROR` | An epoch exists, but no data line follows it. | Check that the file contains `P...` or `V...` lines after the epoch records. |
| `SP3_FILE_MISSING_POSITION_ERROR` | No position record `P` was found. | Check that the file contains position records, for example `PG01 ...` or `PL06 ...`. |
| `SP3_FILE_MISSING_VELOCITY_ERROR` | The file is declared in `V` mode, but no velocity record `V` was found. | Check that velocity records are present when the declared mode is `V`. |
| `SP3_FILE_EOF_ERROR` | The file does not end with `EOF`. | Check that the SP3 file is not truncated. |
| `SP3_FILE_EPOCH_ERROR` | The first data epoch does not match the start epoch declared in the header. | Check the time consistency between the first header line and the first `*` epoch line. |

---

## RINEX Observation errors

These errors concern `.rnx` files, expected as RINEX 2 observation files.

| Code | Cause | Recommended action |
|---|---|---|
| `RINEX_FILE_TOO_SHORT` | The file is too short to be a valid RINEX file. | Check that the file is not truncated. |
| `RINEX_FILE_HEADER_ERROR` | The `RINEX VERSION / TYPE` line is missing, or the header does not contain `END OF HEADER` within the expected limit. | Check that the RINEX header is complete. |
| `RINEX_FILE_VERSION_ERROR` | The RINEX version is missing, invalid, or unsupported. SpaceBench currently expects RINEX 2 for mission observations. | Provide a compatible RINEX 2 observation file. |
| `RINEX_FILE_TYPE_ERROR` | The file is not declared as `OBSERVATION DATA`. | Check that the file is an observation file, not a navigation, clock, or meteorological file. |
| `RINEX_FILE_OBSERVATION_TYPE_ERROR` | The `# / TYPES OF OBSERV` line is missing. | Check that the RINEX header declares the observation types. |
| `RINEX_FILE_OBSERVATION_COUNT_ERROR` | The number of observation types is missing, invalid, or zero. | Check the `# / TYPES OF OBSERV` line, for example `9 L1 L2 C1 ...`. |
| `RINEX_FILE_START_EPOCH_ERROR` | The `TIME OF FIRST OBS` line is missing or invalid. | Check the first observation date in the header. |
| `RINEX_FILE_FIRST_EPOCH_ERROR` | No valid first observation epoch was found after the header. | Check that the data section starts correctly after `END OF HEADER`. |
| `RINEX_FILE_EPOCH_ERROR` | The first data epoch does not match `TIME OF FIRST OBS`. | Check the time consistency between the header and the first epoch. |
| `RINEX_FILE_EPOCH_FLAG_ERROR` | The first epoch flag is invalid or unsupported. | Check the epoch flag field. Expected normal values are usually `0` or `1`. |
| `RINEX_FILE_START_EPOCH_SAT_COUNT_ERROR` | The number of satellites in the first epoch is missing, invalid, or zero. | Check the first epoch line. |
| `RINEX_FILE_FIRST_DATA_ERROR` | The observation data after the first epoch is missing or incomplete. | Check that each satellite has an observation block matching the declared observation types. |

---

## RINEX CLK errors

These errors concern `.clk_30s` files, expected as RINEX Clock v3 files.

| Code | Cause | Recommended action |
|---|---|---|
| `CLK_FILE_HEADER_ERROR` | The `RINEX VERSION / TYPE` line is missing, or the header does not end correctly with `END OF HEADER`. | Check that the CLK header is complete and that the file is not truncated or malformed. |
| `CLK_FILE_VERSION_ERROR` | The RINEX Clock version is missing, invalid, or unsupported. SpaceBench expects RINEX v3. | Provide a compatible RINEX Clock 3 file. |
| `CLK_FILE_TYPE_ERROR` | The file type is not `C`, or the type field is missing. | Check that the file is a RINEX clock file. |
| `CLK_FILE_DATA_ERROR` | No `AS` record was found. | Provide a file containing satellite clock records `AS`, required for POD processing. |
| `CLK_FILE_TIMESTAMP_ERROR` | The timestamp of the first `AS` record is invalid. | Check the first `AS` line, for example `AS G02 2010 07 19 00 00 0.000000 ...`. |

---

## Python plugin errors

These errors concern `.py` files used as custom estimators.

| Code | Cause | Recommended action |
|---|---|---|
| `PY_FILE_SYNTAX_ERROR` | The Python file contains a syntax error. | Fix the syntax of the `.py` file. |
| `PY_FILE_CUSTOM_ESTIMATOR_ERROR` | No `CustomEstimator` class was found. | Define a class named exactly `CustomEstimator`. |
| `PY_FILE_BASE_ESTIMATOR_ERROR` | `CustomEstimator` does not inherit from `BaseEstimator`. | Declare `class CustomEstimator(BaseEstimator):`. |
| `PY_FILE_ESTIMATE_METHOD_ERROR` | The `estimate` method is missing. | Add an `estimate(...)` method inside `CustomEstimator`. |
| `PY_FILE_FORBIDDEN_IMPORT` | The file imports a forbidden module, for example `os`, `sys`, `subprocess`, or `socket`. | Remove dangerous imports. |
| `PY_FILE_FORBIDDEN_CALL` | The file calls a forbidden function, for example `eval`, `exec`, `compile`, `__import__`, `open`, or `input`. | Remove dangerous function calls. |

---

## Validation notes

SpaceBench performs structural pre-validation. It checks that files are readable, consistent with the expected format, and complete enough to be passed to the POD pipeline.

This does not replace a full scientific analysis of the content. For example, an SP3 file may be structurally valid while still containing orbit products of insufficient quality or products that are temporally incompatible with a given mission.

For custom Python plugins, AST validation checks the structure of the code without executing it. It is not a complete security sandbox. Custom plugin execution should be isolated in a controlled environment.
