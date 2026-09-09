from pydantic import BaseModel
from ..enums import *

class RunConfig(BaseModel):
    rinex_file_id : str
    gnss_sp3_file_id : str
    gnss_clk_file_id : str
    rso_file_ids : list[str]
    rinex_path: str
    gnss_sp3_path: str
    gnss_clk_path: str
    rso_sp3_paths: list[str]
    orbital_model : str
    estimator_type : str
    estimator_file_id : str | None = None
    estimator_path: str | None = None
    tolerance: float | None = None
    max_iteration: int | None = None


class RunRequest(BaseModel):
    run_id : str
    config: RunConfig
    metadata : dict

