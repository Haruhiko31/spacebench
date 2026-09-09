from abc import abstractmethod, ABC

from app.services.run_logger import RunLogger
import numpy as np

class BaseEstimator(ABC):
    def __init__(self, config, logger: RunLogger):
        self.config = config
        self.logger = logger
        self.previous_state : np.ndarray | None = None

    @property
    def need_minimum_satellites(self) -> int :
        return 4

    # Kalman filtering which needs previous state
    def get_previous_state(self, initial_state: np.ndarray) -> None:
        self.previous_state = initial_state.copy()

    def post_process(self, estimated_state: list[dict]) -> dict:
        return estimated_state.copy()

    # Class to implement
    @abstractmethod
    def estimate_epoch(self, epoch_obs: dict, initial_state: np.ndarray) -> tuple[np.ndarray, dict]:
        pass
