from datetime import datetime

from pydantic import BaseModel
from .base import FileValidator, FileDescriptor, FileValidationResult, FileValidationError
from ...schemas.pod import Sp3Meta

try:
    from app.models.pod import FileType
    print(f"FileType imported OK: {FileType.sp3}")
except Exception as e:
    print(f"FileType import FAILED: {e}")

class Sp3Validator(FileValidator):
    ext = ".sp3"
    file_type = FileType.sp3

    def validate(self, file: FileDescriptor) -> FileValidationResult:
        issues: list[FileValidationError] = []

        print("-------------------------------------------------------------------------")
        print("[VALIDATION SP3] STARTING VALIDATION...")
        print("-------------------------------------------------------------------------")

        # ═════════════════════════ FILE IS NOT EMPTY AND CAN BE READ
        lines, error = self.read_ascii_lines(file)

        if error:
            return error

        print(f"[VALIDATION SP3] NOT_EMPTY : success !")
        print(f"[VALIDATION SP3] BIN → TEXT : success !")

        # ═════════════════════════ Need at least 3 lines for basic SP3 header validation
        if len(lines) < 3:
            return self.send_error("SP3_FILE_TOO_SHORT", "The file is too short to be a valid SP3 file.", 0)

        first_line = lines[0]
        parts = first_line.split()  # Explode all the blocks from first row

        # Validate first header row shape
        if len(parts) < 7:
            return self.send_error("SP3_FILE_HEADER_ERROR", "The first SP3 header line is incomplete.", 1)

        if len(parts[0]) < 4:
            return self.send_error("SP3_FILE_HEADER_ERROR", "The first SP3 header token is incomplete.", 1)


        # ═════════════════════════ Valid version (#a, #b, #c, #d) + starts with # (e.g. #dV2010 where V is P+V, and P is P-only.)
        version = parts[0][0:2]

        if version not in {"#a", "#b", "#c", "#d"}:
            return self.send_error("SP3_FILE_VERSION_ERROR", "The file version is not valid.", 1)

        print(f"[VALIDATION SP3] Version : success ! [{version}]")

        mode = parts[0][2]  # (P or V)

        if mode not in {"P", "V"}:
            return self.send_error("SP3_FILE_MODE_ERROR", f"The file mode is not valid. Expected P or V, got [{mode}].", 1)

        print(f"[VALIDATION SP3] Mode : success ! [{mode}]")

        # ═════════════════════════ Start epoch from header

        try:
            year = int(parts[0][3:])  # 2010
            month = int(parts[1])
            day = int(parts[2])
            hour = int(parts[3])
            minute = int(parts[4])
            second_float = float(parts[5])
            second_int = int(second_float)
            microsecond = int(round((second_float - second_int) * 1_000_000))

            start_epoch = datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second_int,
                microsecond=microsecond
            )
        except ValueError:
            return self.send_error("SP3_FILE_START_EPOCH_ERROR", "The start epoch in the header is not valid.", 1)

        print(f"[VALIDATION SP3] START EPOCH : success ! [{start_epoch}]")

        # ═════════════════════════ Number of Epochs (e.g. 1682)

        try:
            epoch_count = int(parts[6])
        except (IndexError, ValueError):
            return self.send_error("SP3_FILE_EPOCH_COUNT_ERROR", "The epoch count is missing or invalid.", 1)

        if not (epoch_count > 0):
            return self.send_error("SP3_FILE_EPOCH_COUNT_ERROR", "The file has no epoch.", 1)

        print(f"[VALIDATION SP3] Epoch count : success ! [{epoch_count}]")

        # ═════════════════════════ VERIFY SAT LIST (e.g. G01G02G03 or G01 G02 G03)

        sats = []

        for line in lines:
            if not line.startswith("+"):
                continue

            parts = line.split()

            if len(parts) < 2:
                continue

            # IGS Style (G01G02G03G04G05G06)

            # Exploded sat list (G01 G02 G03 G04 G05 G06)
            sat_list = "".join(parts[2:])

            for i in range(0, len(sat_list), 3):
                sat = sat_list[i:i + 3]

                if len(sat) == 3 and sat[0].isalpha() and sat[1:].isdigit():
                    sats.append(sat)

        #  At least 1 sat (e.g. + 1 L06)
        if len(sats) == 0:
            return self.send_error("SP3_FILE_NUMBER_OF_SATS_ERROR", "There are no satellites.", 3)

        print(f"[VALIDATION SP3] SATS COUNT : success ! [{len(sats)} satellites]")

        # ═════════════════════════ At least one valid epoch (e.g. * 2010 7 18 22 0 0.00000000)

        first_epoch = None
        first_epoch_index = None

        index = 0
        for line in lines:
            if line.startswith("*"):
                first_epoch = line.split()
                first_epoch_index = index
                break

            index += 1

        if first_epoch is None or first_epoch_index is None:
            return self.send_error("SP3_FILE_FIRST_EPOCH_ERROR", "No epoch was found.", 0)

        #print(f"First epoch : {first_epoch}")
        #print(f"First epoch index : {first_epoch_index}")

        try:
            year = int(first_epoch[1])  # 2010
            month = int(first_epoch[2])
            day = int(first_epoch[3])
            hour = int(first_epoch[4])
            minute = int(first_epoch[5])
            second_float = float(first_epoch[6])

            first_epoch_formatted = datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=int(second_float),
            )
        except (IndexError, ValueError):
            return self.send_error("SP3_FILE_FIRST_EPOCH_ERROR", f"The first epoch is not valid. [{first_epoch}]", first_epoch_index + 1)

        print(f"[VALIDATION SP3] VALID EPOCH : success ! [{first_epoch_formatted}]")

        if first_epoch_index + 1 >= len(lines):
            return self.send_error("SP3_FILE_DATA_ERROR", "The file has an epoch but no data row after it.", first_epoch_index + 1)

        first_data_row = lines[first_epoch_index + 1]
        #print(f"First data row : {first_data_row}")

        p_count = 0
        v_count = 0

        #print(f"Len(lines) : {len(lines)}")

        # ═════════════════════════ VERIFY FILE MODE AND INTEGRITY

        for i in range((first_epoch_index + 1), len(lines) - 1):
            if not lines[i].strip():
                continue

            current_line = lines[i][0]

            # print(f"Current line : {current_line}")

            if current_line == 'P':
                p_count += 1

            if current_line == 'V':
                v_count += 1

            # If P-only, it should not contain any V records.
            if mode == 'P':
                if current_line not in {"P", "E", "*"}:
                    return self.send_error("SP3_FILE_MODE_ERROR", f"The mode is P-only, but contains wrong line mode. [{lines[i]}]", i + 1)

            # If V, it should contain P and V.
            if mode == 'V':
                if current_line not in {"P", "V", "E", "*"}:
                    return self.send_error("SP3_FILE_MODE_ERROR", f"The mode is P and V, but contains wrong line mode. [{lines[i]}]", i + 1)

        if not (p_count > 0):
            return self.send_error("SP3_FILE_MISSING_POSITION_ERROR", "The file does not contain any P records.", 0)

        if mode == 'V':
            if not (v_count > 0):
                return self.send_error("SP3_FILE_MISSING_VELOCITY_ERROR", "The mode is P and V, but does not contain any V records.", 0)

        print(f"[VALIDATION SP3] VALID MODE : success !")

        # Position & Velocity binome (e.g. PL06, VL06)

        # ═════════════════════════ file ends with EOF

        last_line = lines[-1].strip()

        if last_line != "EOF":
            return self.send_error("SP3_FILE_EOF_ERROR", "The file is not formed correctly. EOF is missing.", len(lines))

        print(f"[VALIDATION SP3] EOF : success !")

        # start epoch ~= first epoch timestamp
        delta_seconds = abs((first_epoch_formatted - start_epoch).total_seconds())

        if delta_seconds > 1:
            return self.send_error("SP3_FILE_EPOCH_ERROR", f"The first epoch does not correlate to start epoch. [Start epoch : {start_epoch}, First epoch : {first_epoch_formatted}]", first_epoch_index + 1)

        print("[VALIDATION SP3] EPOCH correlate : success !")

        print("-------------------------------------------------------------------------")
        print("[VALIDATION SP3] SUCCESS")
        print("-------------------------------------------------------------------------")

        return FileValidationResult(
            valid=True,
            issues=issues,
            metadata=Sp3Meta(
                version=version,
                mode=mode,
                start_epoch=start_epoch,
                epoch_count=epoch_count,
                satellites=sats,
                first_epoch_index=first_epoch_index,
                p_count=p_count,
                v_count=v_count,
            ).model_dump(mode="json"),
        )
