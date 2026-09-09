from datetime import datetime

from .base import FileValidator, FileDescriptor, FileValidationResult, FileValidationError
from app.models.pod import FileType
from ...schemas.pod import ClkMeta


class ClkValidator(FileValidator):
    ext = ".clk_30s"
    file_type = FileType.clock

    def validate(self, file: FileDescriptor) -> FileValidationResult:
        issues: list[FileValidationError] = []

        print("-------------------------------------------------------------------------")
        print("[VALIDATION CLK] STARTING VALIDATION...")
        print("-------------------------------------------------------------------------")

        # ═════════════════════════ FILE IS NOT EMPTY AND CAN BE READ

        lines, error = self.read_ascii_lines(file)

        if error:
            return error

        print(f"[VALIDATION CLK] NOT_EMPTY : success !")
        print(f"[VALIDATION CLK] BIN → TEXT : success !")

        first_line = lines[0]
        parts = first_line.split()

        # ═════════════════════════ HEADER FIRST LINE VERSION AND FILE TYPE

        if "RINEX VERSION / TYPE" not in first_line:
            return self.send_error("CLK_FILE_HEADER_ERROR", "RINEX VERSION / TYPE is missing.", 1)

        # RINEX VERSION (3)
        try:
            version = int(float(parts[0]))
        except (IndexError, ValueError) as e:
            return self.send_error("CLK_FILE_VERSION_ERROR", f"The RINEX Version is missing or invalid. {e}", 0)

        if not (version == 3):
            return self.send_error("CLK_FILE_VERSION_ERROR", "Only RINEX v3 is supported.", 0)

        print(f"[VALIDATION CLK] RINEX VERSION : success !")

        # CLOCK FILE TYPE
        try:
            file_type = parts[1]
        except IndexError as e:
            return self.send_error("CLK_FILE_TYPE_ERROR", f"The file type is missing. {e}", 1)

        if file_type != "C":
            return self.send_error("CLK_FILE_TYPE_ERROR", "Only Clock file type is supported.", 1)

        print(f"[VALIDATION CLK] FILE TYPE 'C' : success !")

        # ═════════════════════════ END OF HEADER

        end_of_header_index = None

        for i in range(0, len(lines)):
            line = lines[i]

            if "END OF HEADER" in line:
                end_of_header_index = i
                break
            if line.startswith(("AR ", "AS ")): # Data are reached, the header did not stop correctly
                break

        if end_of_header_index is None:
            return self.send_error("CLK_FILE_HEADER_ERROR", "The header is malformed, it does not end with END OF HEADER.", 0)

        print(f"[VALIDATION CLK] END OF HEADER : success !")

        # ═════════════════════════ FIRST 'AS' DATA LINE + PARSE

        first_AS_data_line = None

        for i in range(end_of_header_index + 1, len(lines)):
            line = lines[i]

            if line.startswith("AS "):
                first_AS_data_line = i
                break

        if first_AS_data_line is None:
            return self.send_error("CLK_FILE_DATA_ERROR", "The file does not contain any AS data.", 0)

        print(f"[VALIDATION CLK] AS DATA : success ! [{first_AS_data_line+1}]")

        parts = lines[first_AS_data_line].split()

        try:
            year = int(parts[2])
            month = int(parts[3])
            day = int(parts[4])
            hour = int(parts[5])
            minute = int(parts[6])
            second = float(parts[7])
            second_int = int(second)

            AS_data = datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=int(second), microsecond = int(round((second - second_int) * 1_000_000)))

        except (IndexError, ValueError) as e:
            return self.send_error("CLK_FILE_TIMESTAMP_ERROR", f"The first AS timestamp is invalid. {e}", first_AS_data_line + 1)

        print(f"[VALIDATION CLK] AS DATA PARSING : success ! [{AS_data}]")

        print("-------------------------------------------------------------------------")
        print("[VALIDATION CLK] SUCCESS")
        print("-------------------------------------------------------------------------")
        return FileValidationResult(
            valid=True,
            issues=issues,
            metadata=ClkMeta(
                version=version,
                end_of_header_index=end_of_header_index,
                first_as_line_index=first_AS_data_line,
                first_as_timestamp=AS_data,
            ).model_dump(mode="json"),
        )

