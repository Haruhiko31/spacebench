import numpy as np
from app.estimators.base import BaseEstimator

C = 299792458

class CustomEstimator(BaseEstimator):
    def estimate_epoch(self, epoch_obs, initial_state) -> tuple[np.ndarray, dict]:
        positions = []
        for sv in epoch_obs:
            positions.append(epoch_obs[sv]["sat_pos"])

        avg_pos = np.mean(positions, axis=0)

        state = np.array([avg_pos[0], avg_pos[1], avg_pos[2], 0.0])

        return state, {"iterations_to_stop" : 1, "corrections_history": [0.0]}