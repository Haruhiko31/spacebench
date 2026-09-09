# Backend

The backend is the orchestration layer of SpaceBench. It receives files from the frontend, validates them immediately, stores validation metadata in PostgreSQL, creates analysis runs, and launches the POD engine.

Pre-validation belongs here, not in the POD engine. It happens before a run starts and before the scientific files are parsed by `georinex`.

---

## Responsibilities

| Responsibility | Implementation |
|----------------|----------------|
| File upload | `backend/app/routers/files/files.py` |
| Per-file pre-validation | `backend/app/validators/upload` |
| Validation metadata persistence | `UploadedFile.validation_metadata` |
| Run creation | `backend/app/routers/runs/run.py` |
| File grouping per run | `organize_run_files()` |
| POD engine launch | `LaunchRunService` |
| Run logs API | `GET /api/runs/{run_id}/logs` |

---

## Upload-Time Pre-Validation

When a file is uploaded through `POST /api/files/upload`, the backend:

1. checks the extension;
2. stores the file temporarily;
3. selects the matching validator;
4. validates the file content;
5. deletes the file and returns HTTP `422` if validation fails;
6. stores the file record and validation metadata if validation succeeds.

The validators follow a common template through `FileValidator`:

```python
class FileValidator(ABC):
    ext: str
    file_type: FileType

    def read_ascii_lines(...)
    def send_error(...)
    def parse_epoch(...)

    @abstractmethod
    def validate(...)
```

The concrete validators are selected through a strategy map:

| File type | Extension | Validator |
|-----------|-----------|-----------|
| RINEX observations | `.rnx` | `RnxValidator` |
| SP3 orbit file | `.sp3` | `Sp3Validator` |
| RINEX clock file | `.clk_30s` | `ClkValidator` |
| Custom estimator | `.py` | `PythonValidator` |

---

## Validator Outputs

Each validator returns:

```python
class FileValidationResult(BaseModel):
    valid: bool
    issues: list[FileValidationError]
    metadata: dict
```

Validation errors are structured with a code, message, and line number. This makes frontend feedback deterministic and easier to document.

### RINEX Validator

`RnxValidator` currently checks:

| Check | Purpose |
|-------|---------|
| ASCII decoding and non-empty content | Reject unreadable files |
| `RINEX VERSION / TYPE` header | Confirm RINEX format |
| RINEX version 2 | Current supported observation format |
| `OBSERVATION DATA` type | Reject navigation or unrelated RINEX files |
| `# / TYPES OF OBSERV` | Confirm observation structure |
| `END OF HEADER` | Confirm header integrity |
| `TIME OF FIRST OBS` | Extract start epoch |
| first observation epoch | Confirm data exists |
| epoch/header consistency | Ensure first epoch matches header time |
| epoch flag and satellite count | Reject unsupported first epoch |
| first satellite observation block | Confirm observation fields are present |

Stored metadata includes the RINEX version, header end line, start epoch, observation count, first epoch index, first epoch satellite count, continuation line count, and epoch flag.

### SP3 Validator

`Sp3Validator` currently checks:

| Check | Purpose |
|-------|---------|
| ASCII decoding and non-empty content | Reject unreadable files |
| SP3 version `#a` to `#d` | Confirm supported SP3 family |
| mode `P` or `V` | Confirm position-only or position/velocity file |
| header start epoch | Extract temporal metadata |
| epoch count | Reject empty orbit products |
| satellite list | Confirm at least one satellite |
| first epoch | Confirm data section exists |
| position and velocity records | Check consistency with `P` or `V` mode |
| `EOF` marker | Confirm file closure |
| header/data epoch consistency | Detect mismatched headers |

Stored metadata includes version, mode, start epoch, epoch count, satellite identifiers, first epoch index, position record count, and velocity record count.

### CLK Validator

`ClkValidator` currently checks:

| Check | Purpose |
|-------|---------|
| ASCII decoding and non-empty content | Reject unreadable files |
| RINEX version 3 | Current supported clock format |
| clock file type `C` | Reject non-clock RINEX files |
| `END OF HEADER` | Confirm header integrity |
| first `AS` record | Confirm satellite clock data exists |
| first `AS` timestamp | Extract clock start metadata |

Stored metadata includes version, header end line, first `AS` line index, and first `AS` timestamp.

### Python Estimator Validator

`PythonValidator` currently parses custom estimator files with Python `ast`.

It checks:

| Check | Purpose |
|-------|---------|
| UTF-8 decoding and non-empty content | Reject unreadable Python files |
| syntax validity | Reject files that cannot be parsed |
| `CustomEstimator` class | Enforce expected extension point |
| inheritance from `BaseEstimator` | Enforce estimator interface |
| `estimate()` method | Confirm callable estimation entry point |
| forbidden imports | Block `os`, `sys`, `subprocess`, `socket` |
| forbidden calls | Block `eval`, `exec`, `compile`, `__import__`, `open`, `input` |

This is a pre-validation layer only. It reduces obvious risk but is not a complete sandbox.

---

## Run Creation and Engine Launch

When the frontend creates a run through `POST /api/runs`, the backend:

1. creates the `Run` database record;
2. links the selected RSO files through `RunRsoFile`;
3. moves uploaded files into a run-specific directory;
4. loads each file's validation metadata;
5. builds the POD engine payload;
6. launches the engine asynchronously.

The payload sent to the POD engine contains both file paths and validation metadata:

```python
metadata = {
    "rinex": rinex_file.validation_metadata,
    "gnss_sp3": gnss_sp3_file.validation_metadata,
    "rso_sp3": rso_metadata,
    "clk": clk_file.validation_metadata,
}
```

The config is also sent to the POD engine.

```python
config = {
    "rinex_file_id": run.rinex_file_id,
    "gnss_sp3_file_id": run.gnss_sp3_file_id,
    "gnss_clk_file_id": run.gnss_clk_file_id,
    "rso_file_ids": rso_file_ids,
    "rinex_path": rinex_file.stored_path,
    "gnss_sp3_path": gnss_sp3_file.stored_path,
    "gnss_clk_path": clk_file.stored_path,
    "rso_sp3_paths": rso_paths,
    "orbital_model": run.orbital_model,
    "estimator_type": run.estimator_type,
    "estimator_file_id": estimator_file_id,
    "estimator_path": estimator_path,
    "max_iteration": run.max_iteration,
    "tolerance": run.tolerance
}
```

The engine then performs cross-file validation using this metadata before parsing the scientific content.

---

## Why This Split Matters

Keeping pre-validation in the backend has three advantages:

| Advantage | Explanation |
|-----------|-------------|
| Immediate frontend feedback | Invalid files fail during upload, before the user launches a run |
| Cleaner engine | The POD engine can focus on scientific processing |
| Better traceability | Per-file metadata is stored once and reused when creating runs |

The POD engine should still validate run-level consistency, because a set of individually valid files can still be scientifically incompatible.
