from datetime import datetime
from pydantic import BaseModel


class Sp3Meta(BaseModel):
    version: str              # "#c", "#d"
    mode: str                 # "P" or "V"
    start_epoch: datetime
    epoch_count: int
    satellites: list[str]     # ["G01", "G02", "L06", ...]
    first_epoch_index: int
    p_count: int
    v_count: int

class RinexMeta(BaseModel):
    version: int                    # 2
    end_of_header_index: int
    start_epoch: datetime
    observation_type_count: int
    first_epoch_index: int
    first_epoch_sat_count: int
    sat_continuation_lines: int
    epoch_flag: int

class ClkMeta(BaseModel):
    version: int                  # 3
    end_of_header_index: int
    first_as_line_index: int
    first_as_timestamp: datetime
