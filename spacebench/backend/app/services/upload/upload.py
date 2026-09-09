from app.validators.upload import Sp3Validator, RnxValidator, ClkValidator, FileDescriptor
from app.models.pod import FileType
from app.validators.upload.py import PythonValidator


# ══ Strategy Pattern ══════════════════════════
class FileValidationService:
    def __init__(self) -> None:
        self.validators = {
            FileType.sp3: Sp3Validator(),
            FileType.rinex: RnxValidator(),
            FileType.clock: ClkValidator(),
            FileType.estimator: PythonValidator()
        }

        # Verify if all the FileType has an implemented Validator
        # If not, warn the user.
        missing_validators = set(FileType) - set(self.validators)
        if missing_validators:
            missing_names = ", ".join(missing_validators)
            raise ValueError(f"Missing validators : {missing_names}")

    def validate(self, file: FileDescriptor):
        try:
            validator = self.validators[file.file_type]
        except KeyError as e:
            raise ValueError(f"Invalid file type {file.file_type}") from e

        return validator.validate(file)