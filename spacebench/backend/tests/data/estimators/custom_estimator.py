# custom_estimator.py
from x import y

from pydantic.dataclasses import dataclass


@dataclass
class BaseEstimator:
    field_1:      int
    field_2:      any

# ══ Your implementation ══════════════════════════════
class CustomEstimator(BaseEstimator):

    def estimate(self, lines):
        pass
