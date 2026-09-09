from .EKF import EKFEstimator
from .KF import KFEstimator
from .LSQ import LSQEstimator
from .UKF import UKFEstimator
from .base import BaseEstimator
from .custom import CustomEstimator

REGISTRY: dict[str, type[BaseEstimator]] = {
    "BLSQ": LSQEstimator,
    "KF": KFEstimator,
    "UKF": UKFEstimator,
    "EKF": EKFEstimator,
    "custom": CustomEstimator
}

def get_estimator(name: str) -> type[BaseEstimator]:
    if name not in REGISTRY:
        raise ValueError(f"Unknown estimator {name}")
    else:
        return REGISTRY[name]