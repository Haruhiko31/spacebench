from datetime import datetime

from app.enums import LogLevel
from pydantic import BaseModel

from app.models.pod import FileType, OrbitalModel, EstimatorType, RunStatus


class FileResponse(BaseModel):
    id:            str
    original_name: str
    file_type:     FileType
    uploaded_at:   datetime
    model_config = {"from_attributes": True}


class RunCreate(BaseModel):
    name:              str
    mission_name:      str

    mission_year: int
    mission_day : int

    orbital_model:     OrbitalModel
    estimator_type:    EstimatorType

    rinex_file_id: str
    gnss_sp3_file_id: str
    gnss_clk_file_id: str
    rso_file_ids: list[str]
    estimator_file_id: str | None = None

    tolerance: float | None = None
    max_iteration: int | None = None

    rms_3d:            float | None = None
    rms_radial:        float | None = None
    rms_along:         float | None = None
    rms_cross:         float | None = None



class RunResponse(BaseModel):
    id:                str
    name:              str
    mission_name:      str
    mission_year:      int
    mission_day:       int
    orbital_model:     OrbitalModel
    estimator_type:    EstimatorType
    status:            RunStatus
    created_at:        datetime
    gnss_sp3_file_id:  str | None
    gnss_clk_file_id:  str | None
    rinex_file_id:     str | None
    rso_file_ids:      list[str]
    estimator_file_id: str | None
    estimator_file_id: str | None
    max_iteration :    int | None
    tolerance :        float | None
    rms_3d:            float | None
    rms_radial:        float | None
    rms_along:         float | None
    rms_cross:         float | None
    model_config = {"from_attributes": True}


class RunLogsResponse(BaseModel):
    run_id: str
    level: LogLevel
    phase: str
    created_at: datetime
    message: str
    model_config = {"from_attributes": True}
