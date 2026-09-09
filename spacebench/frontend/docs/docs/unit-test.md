# Unit Tests

Unit tests are organized by application component. The tables below present the available tests, the relevant endpoint (when applicable), their objective, and the expected behavior.

---

## Backend Unit Tests

### Health & Documentation

| Test | Endpoint | Description | Expected |
|------|----------|-------------|----------|
| `test_health_returns_200` | `/health` | Verifies that the backend health endpoint is reachable. | HTTP 200 |
| `test_health_response_body` | `/health` | Verifies that the response contains a `status` field with the value `ok`. | `status = ok` |
| `test_redoc_returns_200` | `/api/redoc` | Verifies that the ReDoc documentation is accessible. | HTTP 200 |
| `test_swagger_returns_200` | `/api/docs` | Verifies that the Swagger documentation is accessible. | HTTP 200 |

### File Management

| Test | Endpoint | Description | Expected |
|------|----------|-------------|----------|
| `test_upload_valid_file` | `/api/files/upload` | Verifies that a valid file can be uploaded and that the response contains an identifier and the original filename. | HTTP 201 |
| `test_upload_bad_extension` | `/api/files/upload` | Verifies that a file with an unsupported extension is rejected. | HTTP 400 |
| `test_upload_invalid_content` | `/api/files/upload` | Verifies that a file with invalid content is rejected, even if its extension is correct. | HTTP 422 |
| `test_download_existing_file` | `/api/files/{id}/download` | Verifies that an existing file can be downloaded using its identifier. | HTTP 200 |
| `test_download_non_existing_file` | `/api/files/{id}/download` | Verifies that attempting to download a non-existent file returns an error. | HTTP 404 |
| `test_bulk_download_existing` | `/api/files/bulk/download` | Verifies that bulk download works when a list of valid identifiers is provided. | HTTP 200 |
| `test_bulk_download_non_existing` | `/api/files/bulk/download` | Verifies that bulk download fails when a non-existent file identifier is provided. | HTTP 404 |
| `test_bulk_download_empty` | `/api/files/bulk/download` | Verifies that an empty list of identifiers is rejected during bulk download. | HTTP 400 |

### Run Management

| Test | Endpoint | Description | Expected |
|------|----------|-------------|----------|
| `test_run_valid` | `/api/runs` | Verifies that a valid run can be created with the required parameters. | HTTP 201 |
| `test_run_invalid` | `/api/runs` | Verifies that an incomplete or invalid run is rejected by the API. | HTTP 422 |
| `test_get_run_count` | `/api/runs/count` | Verifies that the total number of runs can be retrieved. | HTTP 200 |
| `test_get_run_count_filtered_by_statut` | `/api/runs/count?statuses=pending` | Verifies that the run count can be filtered by status. | HTTP 200 |
| `test_get_run_filtered_by_unknown_status` | `/api/runs/count?statuses=unknown_status` | Verifies that an unknown status is rejected when counting runs. | HTTP 422 |
| `test_get_list_runs` | `/api/runs` | Verifies that the list of runs can be retrieved. | HTTP 200 |
| `test_get_existing_run` | `/api/runs/{id}` | Verifies that an existing run can be retrieved using its identifier. | HTTP 200 |
| `test_get_non_existing_run` | `/api/runs/9999999` | Verifies that an error is returned when a non-existent run is requested. | HTTP 404 |
| `test_list_runs_with_sort` | `/api/runs?sort_by=name&sort_order=asc&limit=5` | Verifies that the run list can be sorted and limited. | HTTP 200 |
| `test_list_runs_filtered_by_status` | `/api/runs?statuses=pending` | Verifies that the run list can be filtered by status. | HTTP 200 |
| `test_list_runs_filtered_by_unknown_status` | `/api/runs?statuses=unknown_status` | Verifies that an unknown status is rejected when filtering runs. | HTTP 422 |
| `test_get_run_logs` | `/api/runs/{id}/logs` | Verifies the API behavior when no execution logs are available for an existing run. | HTTP 404 |
| `test_get_run_logs_non_existing` | `/api/runs/9999999/logs` | Verifies that an error is returned when requesting logs for a non-existent run. | HTTP 404 |

---

## POD Engine Unit Tests

### Health & Endpoint

| Test | Endpoint | Description | Expected |
|------|----------|-------------|----------|
| `test_health_returns_200` | `/health` | Verifies that the POD engine health endpoint is reachable. | HTTP 200 |
| `test_health_response_body` | `/health` | Verifies that the POD engine response contains a `status` field with the value `ok`. | `status = ok` |
| `test_analysis_returns_200` | `/api/runs?tested=true` | Verifies that a POD analysis can be launched with a valid payload. | HTTP 200 |
| `test_analysis_missing_payload` | `/api/runs?tested=true` | Verifies that a POD analysis request without a payload is rejected. | HTTP 422 |

### Initialization & Cross-Validation

| Test | Function | Description | Expected |
|------|----------|-------------|----------|
| `test_init_passes` | `init` | Verifies that the initialization phase returns a valid result when all required metadata is provided. | Non-null result |
| `test_init_not_all` | `init` | Verifies that initialization fails when a required metadata field, such as the GNSS clock file, is missing. | `None` |
| `test_init_missing_dict_key` | `init` | Verifies that initialization fails when a required key is missing from the metadata dictionary. | `None` |
| `test_cross_validate_passes` | `cross_validate` | Verifies that cross-validation accepts a consistent set of metadata. | `True` |
| `test_cross_validate_small_offset_sp3_ok` | `cross_validate` | Verifies that an acceptable time offset for the GNSS SP3 file is tolerated. | `True` |
| `test_cross_validate_small_offset_clk_ok` | `cross_validate` | Verifies that an acceptable time offset for the GNSS clock file is tolerated. | `True` |
| `test_cross_validate_small_offset_sp3_60s_ok` | `cross_validate` | Verifies that a 60-second offset for the GNSS SP3 file is still accepted. | `True` |
| `test_cross_validate_small_offset_clk_60s_ok` | `cross_validate` | Verifies that a 60-second offset for the GNSS clock file is still accepted. | `True` |
| `test_cross_validate_small_offset_sp3_nok` | `cross_validate` | Verifies that an offset exceeding the allowed threshold for the GNSS SP3 file is rejected. | `False` |
| `test_cross_validate_small_offset_clk_nok` | `cross_validate` | Verifies that an offset exceeding the allowed threshold for the GNSS clock file is rejected. | `False` |
| `test_cross_validate_rso_earliest_one_arc_ok` | `cross_validate` | Verifies that validation accepts an RSO observation correctly covering the beginning of the time arc. | `True` |
| `test_cross_validate_rso_earliest_nok` | `cross_validate` | Verifies that validation rejects RSO observations whose start time is too late. | `False` |
| `test_cross_validate_rso_latest_nok` | `cross_validate` | Verifies that validation rejects RSO observations whose time coverage does not extend far enough. | `False` |
| `test_cross_validate_diff_clk_sp3_nok` | `cross_validate` | Verifies that validation fails when the SP3 and CLK GNSS files have an inconsistent time offset. | `False` |

### Parsing, Interpolation & Estimation

| Test | Function | Description | Expected |
|------|----------|-------------|----------|
| `test_parse_clk_reads_sats` | `parse_clk` | Verifies that the GNSS clock file is correctly read and that the expected satellites are detected. | Satellites present |
| `test_parse_clk_correct_bias` | `parse_clk` | Verifies that the clock biases extracted from the CLK file match the expected values. | Correct values |
| `test_parse_clk_skip_AR` | `parse_clk` | Verifies that non-satellite entries, such as AR records, are ignored during parsing. | Entry ignored |
| `test_interpolate_clk_mid` | `interpolate_clk` | Verifies that clock interpolation returns a correct intermediate value between two known epochs. | Interpolated value |
| `test_interpolate_clk_known_epoch` | `interpolate_clk` | Verifies that interpolation directly returns the known value when an exact epoch is requested. | Exact value |
| `test_interpolate_sp3_skips_missing_sv_value` | `interpolate_sp3` | Verifies that SP3 interpolation skips a satellite when an insufficient number of points is available. | Satellite skipped |
| `test_get_existing_estimator` | `get_estimator` | Verifies that an existing estimator is correctly resolved from its identifier. | Estimator returned |
| `test_get_non_existing_estimator` | `get_estimator` | Verifies that an error is raised when an unknown estimator is requested. | `ValueError` |
| `test_get_rso_epoch_data_passed` | `get_rso_epoch_data` | Verifies that RSO coordinates are correctly retrieved for an existing epoch. | RSO coordinates |
| `test_get_rso_epoch_data_unknown` | `get_rso_epoch_data` | Verifies that no data is returned when a non-existent RSO epoch is requested. | `None` |
| `test_initial_rso_state_passed` | `get_initial_RSO_state` | Verifies that the initial RSO state is correctly built from an existing epoch. | State vector |
| `test_initial_rso_state_missing_epoch` | `get_initial_RSO_state` | Verifies that an error is raised when a non-existent epoch is used to build the initial RSO state. | `ValueError` |