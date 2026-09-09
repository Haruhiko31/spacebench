import numpy as np
from .base import BaseEstimator
import os
import importlib.util

class CustomEstimator(BaseEstimator):

    def __init__(self,config, logger, plugin_path: str):
        super().__init__(config,logger)

        if not os.path.isfile(plugin_path):
            raise FileNotFoundError(f"Plugin not found: {plugin_path}")

        spec = importlib.util.spec_from_file_location("user_estimator", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        estimator_selector = None
        for name in dir(module):
            attr = getattr(module, name)
            if isinstance(attr, type) and issubclass(attr, BaseEstimator) and attr is not BaseEstimator:
                estimator_selector = attr
                break

        if estimator_selector is None:
            raise ValueError(f"No BaseEstimator subclass found in {plugin_path}")

        self.plugin = estimator_selector(config=config, logger=logger)

    def estimate_epoch(self, epoch_obs, initial_state) -> tuple[np.ndarray, dict]:
        return self.plugin.estimate_epoch(epoch_obs, initial_state)

