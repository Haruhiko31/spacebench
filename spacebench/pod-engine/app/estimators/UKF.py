import numpy as np
from .base import BaseEstimator


class UKFEstimator(BaseEstimator):

    def estimate_epoch(self, epoch_obs, initial_state) -> tuple[np.ndarray, dict]:
        pass

