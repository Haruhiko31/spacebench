from abc import abstractmethod, ABC
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from dataclasses import dataclass
from app.models.pod import FileType


@dataclass(frozen=True)
class FileDescriptor:
    id: str
    path: Path
    file_type: str
    original_name: str


class FileValidationError(BaseModel):
    code: str
    message: str
    line: int


class FileValidationResult(BaseModel):
    valid: bool
    issues: list[FileValidationError] = []
    metadata: dict = []


# Any subclass should implement validate()

class FileValidator(ABC):
    ext: str            # Extension
    file_type: FileType

    # Read the file first and assert if empty or not.
    def read_ascii_lines(self, file: FileDescriptor) -> tuple[list[str] | None, FileValidationResult | None]:
        raw = file.path.read_bytes()

        if not raw.strip():
            return None, FileValidationResult(
                valid=False,
                issues=[
                    FileValidationError(
                        code="FILE_EMPTY",
                        message="The file is empty.",
                        line=0,
                    )
                ],
            )



        print(f"This ext : {self.ext}")
        try:
            if(self.ext == '.py'):
                text = raw.decode('utf-8')
            else:
                text = raw.decode("ascii")
            lines = text.splitlines()
        except UnicodeDecodeError:
            return None, FileValidationResult(
                valid=False,
                issues=[
                    FileValidationError(
                        code="COMMON_FILE_DECODE_ERROR",
                        message="The file cannot be decoded.",
                        line=0,
                    )
                ],
            )

        return lines, None

    # Use to send error
    def send_error(self, code: str, message: str, line: int = 0):
        return FileValidationResult(
            valid=False,
            issues=[
                FileValidationError(
                    code=code,
                    message=message,
                    line=line,
                )
            ],
        )

    # Pre-validate a date verifying its parsability
    def parse_epoch(self, year: int, month: int, day: int, hour: int, minute: int, second_float: float) -> tuple[bool, Any | datetime] | bool:

        try:
            year = year  # 2010
            month = month
            day = day
            hour = hour
            minute = minute
            second_float = second_float
            second_int = int(second_float)
            microsecond = int(round((second_float - second_int)) * 1_000_000)

            start_epoch = datetime(
                year=year,
                month=month,
                day=day,
                hour=hour,
                minute=minute,
                second=second_int,
                microsecond=microsecond
            )

            return True, start_epoch
        except ValueError:
            return False

    @abstractmethod
    def validate(self, file: FileDescriptor) -> FileValidationResult:
        pass
