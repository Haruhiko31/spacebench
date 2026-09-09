import math
from datetime import datetime

from .base import FileValidator, FileDescriptor, FileValidationResult, FileValidationError
from app.models.pod import FileType
from ...schemas.pod import RinexMeta


class RnxValidator(FileValidator):
    ext = ".rnx"
    file_type = FileType.rinex

    def validate(self, file: FileDescriptor) -> FileValidationResult:
        issues: list[FileValidationError] = []

        print("-------------------------------------------------------------------------")
        print("[VALIDATION RINEX] STARTING VALIDATION...")
        print("-------------------------------------------------------------------------")

        # ═════════════════════════ FILE IS NOT EMPTY AND CAN BE READ
        lines, error = self.read_ascii_lines(file)

        if error:
            return error

        print(f"[VALIDATION RINEX] NOT_EMPTY : success !")
        print(f"[VALIDATION RINEX] BIN → TEXT : success !")

        if len(lines) < 2:
            return self.send_error("RINEX_FILE_TOO_SHORT", "The file is too short to be a valid RINEX file.", 0)

        first_line = lines[0]
        parts = first_line.split()

        # ═════════════════════════ HEADER FIRST LINE VERSION AND FILE TYPE

        if "RINEX VERSION / TYPE" not in first_line:
            return self.send_error("RINEX_FILE_HEADER_ERROR", "RINEX VERSION / TYPE is missing.", 1)

        # RINEX VERSION (2)
        try:
            version = int(float(parts[0]))
        except (IndexError, ValueError) as e:
            return self.send_error("RINEX_FILE_VERSION_ERROR", f"The RINEX Version is missing or invalid. {e}", 1)

        if not (version == 2):
            return self.send_error("RINEX_FILE_VERSION_ERROR", "Only RINEX v2 is supported.", 1)

        print(f"[VALIDATION RINEX] RINEX VERSION : success ! [{version}]")

        # ═════════════════════════ DATA TYPE (e.g. OBSERVATION DATA)

        if "OBSERVATION DATA" not in first_line:
            return self.send_error("RINEX_FILE_TYPE_ERROR", f"File type not supported. [{first_line}]", 1)

        print(f"[VALIDATION RINEX] FILE TYPE : success ! [OBSERVATION DATA]")

        # ═════════════════════════ TYPES OF OBSERVATION (e.g. 9 L1 L2 C1 P1 P2 LP1 SA S1 S2)

        observation_line_index = None

        for i in range(0, len(lines)):
            line = lines[i]

            if "# / TYPES OF OBSERV" in line:
                observation_line_index = i
                break

        if observation_line_index is None:
            return self.send_error("RINEX_FILE_OBSERVATION_TYPE_ERROR", "There is no # / TYPES OF OBSERV line.", 0)

        observation_line_data = lines[observation_line_index].split()

        try:
            observation_type_count = int(observation_line_data[0])
        except (IndexError, ValueError):
            return self.send_error(
                "RINEX_FILE_OBSERVATION_COUNT_ERROR",
                f"The observation type count is invalid. [{observation_line_data}]",
                observation_line_index + 1,
            )

        if not (observation_type_count > 0):
            return self.send_error(
                "RINEX_FILE_OBSERVATION_COUNT_ERROR",
                f"There is no observation type. [{observation_type_count}]",
                observation_line_index + 1,
            )

        print(f"[VALIDATION RINEX] NUMBER OF TYPE OF OBSERV : success ! [{observation_type_count}]")

        # ═════════════════════════ END OF HEADER

        end_of_header_index = None
        max_header_lines = 500

        for i in range(0, min(len(lines), max_header_lines)):
            line = lines[i]

            if "END OF HEADER" in line:
                end_of_header_index = i
                break

        if end_of_header_index is None:
            return self.send_error(
                "RINEX_FILE_HEADER_ERROR",
                f"The header is malformed, END OF HEADER was not found in the first {max_header_lines} lines.",
                0,
            )

        print(f"[VALIDATION RINEX] END OF HEADER : success ! [Line {end_of_header_index + 1}]")

        # ═════════════════════════ START EPOCH FROM HEADER

        start_epoch = None
        start_epoch_index = None
        star_epoch_parseable = False

        for i in range(0, end_of_header_index + 1):
            line = lines[i]

            if "TIME OF FIRST OBS" in line:
                start_epoch_index = i
                break

        if start_epoch_index is None:
            return self.send_error("RINEX_FILE_START_EPOCH_ERROR", "TIME OF FIRST OBS is missing.", 0)

        parts = lines[start_epoch_index].split()

        try:
            star_epoch_parseable, start_epoch = self.parse_epoch(
                year=int(parts[0]),
                month=int(parts[1]),
                day=int(parts[2]),
                hour=int(parts[3]),
                minute=int(parts[4]),
                second_float=float(parts[5]),
            )
        except (IndexError, ValueError):
            return self.send_error(
                "RINEX_FILE_START_EPOCH_ERROR",
                f"The start epoch in the header is not valid. Got {parts}",
                start_epoch_index + 1,
            )

        if start_epoch is None:
            return self.send_error(
                "RINEX_FILE_START_EPOCH_ERROR",
                f"The start epoch in the header is not valid. Got {parts}",
                start_epoch_index + 1,
            )

        print(f"[VALIDATION RINEX] START EPOCH : success ! [{start_epoch}]")

        # ═════════════════════════ FIRST OBSERVATION EPOCH EXISTS AND IS PARSEABLE

        first_epoch_index = None
        first_epoch_parseable = False

        for i in range(end_of_header_index + 1, len(lines)):
            if not lines[i].strip():
                continue

            first_epoch_index = i
            break

        if first_epoch_index is None:
            return self.send_error("RINEX_FILE_FIRST_EPOCH_ERROR", "There is no observation epoch after END OF HEADER.", 0)

        parts = lines[first_epoch_index].split()

        try:
            year = int(parts[0])

            # RINEX 2 uses two-digit years.
            # 80-99 => 1980-1999, 00-79 => 2000-2079.
            if year >= 80:
                year += 1900
            else:
                year += 2000

            first_epoch_parseable, first_epoch = self.parse_epoch(
                year=year,
                month=int(parts[1]),
                day=int(parts[2]),
                hour=int(parts[3]),
                minute=int(parts[4]),
                second_float=float(parts[5]),
            )
        except (IndexError, ValueError):
            return self.send_error(
                "RINEX_FILE_FIRST_EPOCH_ERROR",
                f"The first epoch in the data section is not valid. Got {parts}",
                first_epoch_index + 1,
            )

        if first_epoch is None:
            return self.send_error(
                "RINEX_FILE_FIRST_EPOCH_ERROR",
                f"The first epoch in the data section is not valid. Got {parts}",
                first_epoch_index + 1,
            )

        print(f"[VALIDATION RINEX] FIRST EPOCH : success ! [{first_epoch}]")

        # ═════════════════════════ START EPOCH ~= FIRST OBSERVATION EPOCH

        delta_seconds = abs((first_epoch - start_epoch).total_seconds())

        if delta_seconds > 1:
            return self.send_error(
                "RINEX_FILE_EPOCH_ERROR",
                f"The first epoch does not correlate to TIME OF FIRST OBS. [Header : {start_epoch}, First epoch : {first_epoch}]",
                first_epoch_index + 1,
            )

        print(f"[VALIDATION RINEX] EPOCH CORRELATE : success !")

        # ═════════════════════════ EPOCH FLAG

        try:
            epoch_flag = int(parts[6])
        except (IndexError, ValueError):
            return self.send_error(
                "RINEX_FILE_EPOCH_FLAG_ERROR",
                f"The epoch flag is invalid. Got {parts}",
                first_epoch_index + 1,
            )

        if epoch_flag not in {0, 1}:
            return self.send_error(
                "RINEX_FILE_EPOCH_FLAG_ERROR",
                f"The first epoch flag is not supported. Got {epoch_flag}",
                first_epoch_index + 1,
            )

        print(f"[VALIDATION RINEX] FIRST EPOCH FLAG : success ! [{epoch_flag}]")

        # ═════════════════════════ ONE SAT EXISTS IN FIRST EPOCH

        try:
            first_epoch_sat_count_int = int(parts[7])
        except (IndexError, ValueError):
            return self.send_error(
                "RINEX_FILE_START_EPOCH_SAT_COUNT_ERROR",
                f"The sats count in first epoch line is not valid. Got {parts}",
                first_epoch_index + 1,
            )

        if not (first_epoch_sat_count_int > 0):
            return self.send_error(
                "RINEX_FILE_START_EPOCH_SAT_COUNT_ERROR",
                f"There are no satellites in the first epoch line. Got {first_epoch_sat_count_int}",
                first_epoch_index + 1,
            )

        print(f"[VALIDATION RINEX] FIRST EPOCH SAT COUNT : success ! [{first_epoch_sat_count_int}]")

        # ═════════════════════════ HANDLE POSSIBLE SATELLITE LIST CONTINUATION LINES

        # RINEX 2 epoch lines can hold up to 12 satellite IDs.
        sat_continuation_lines = max(0, math.ceil(first_epoch_sat_count_int / 12) - 1)

        first_data_index = first_epoch_index + 1 + sat_continuation_lines

        if first_data_index >= len(lines):
            return self.send_error(
                "RINEX_FILE_FIRST_DATA_ERROR",
                "There is no observation data after the first epoch.",
                first_epoch_index + 1,
            )

        # ═════════════════════════ ONE DATA LINE EXISTS AFTER EPOCH

        first_data_parts = lines[first_data_index].split()

        if not first_data_parts and not lines[first_data_index].strip():
            return self.send_error(
                "RINEX_FILE_FIRST_DATA_ERROR",
                "There is no data in the file.",
                first_data_index + 1,
            )

        print(f"[VALIDATION RINEX] FIRST OBSERVATION EXISTS : success ! [Line {first_data_index + 1}]")

        # ═════════════════════════ NUMBER OF TYPES OF OBSERVATION = NUMBER OF DATA IN FIRST SATELLITE BLOCK

        lines_per_sat = math.ceil(observation_type_count / 5)

        first_sat_obs_lines = lines[first_data_index:first_data_index + lines_per_sat]

        if len(first_sat_obs_lines) < lines_per_sat:
            return self.send_error(
                "RINEX_FILE_FIRST_DATA_ERROR",
                "The first satellite observation block is incomplete.",
                first_data_index + 1,
            )

        obs_objects = []

        # RINEX 2 observation records are fixed-width.
        # Each observation field is 16 characters.
        # Usually, 5 fields per physical line.
        for obs_line in first_sat_obs_lines:
            for j in range(0, 80, 16):
                obs_objects.append(obs_line[j:j + 16])

                if len(obs_objects) == observation_type_count:
                    break

            if len(obs_objects) == observation_type_count:
                break

        if not (len(obs_objects) == observation_type_count):
            return self.send_error(
                "RINEX_FILE_FIRST_DATA_ERROR",
                f"The number of observation fields does not correlate to # of types of observation. "
                f"Got length {len(obs_objects)} for {obs_objects}",
                first_data_index + 1,
            )

        print(f"[VALIDATION RINEX] FIRST OBSERVATION COUNT : success ! [{len(obs_objects)}]")

        print("-------------------------------------------------------------------------")
        print("[VALIDATION RINEX] SUCCESS")
        print("-------------------------------------------------------------------------")

        print(f"Rinex epoch => {start_epoch.isoformat()}")

        return FileValidationResult(
            valid=True,
            issues=issues,
            metadata=RinexMeta(
                version=version,
                end_of_header_index=end_of_header_index,
                start_epoch=start_epoch,
                observation_type_count=observation_type_count,
                first_epoch_index=first_epoch_index,
                first_epoch_sat_count=first_epoch_sat_count_int,
                sat_continuation_lines=sat_continuation_lines,
                epoch_flag=epoch_flag,
            ).model_dump(mode="json"),
        )