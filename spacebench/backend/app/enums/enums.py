from enum import Enum as PyEnum


class FileType(str, PyEnum):
    sp3 = "sp3"
    rinex = "rinex"
    estimator = "estimator"
    clock = "clock"


class OrbitalModel(str, PyEnum):
    kinematic = "kinematic"
    dynamic = "dynamic"
    reduced_dynamic = "reduced_dynamic"


class EstimatorType(str, PyEnum):
    least_squares = "BLSQ"
    kalman = "KF"
    unscented_kalman = "UKF"
    extended_kalman = "EKF"
    custom = "custom"

class LogLevel(str, PyEnum):
    info = "info"
    success = "success"
    warning = "warning"
    error = "error"

class RunPhase(str, PyEnum):
    init = "init"
    validation = "validation"
    parsing = "parsing"
    estimation = "estimation"
    results = "results"


class RunStatus(str, PyEnum):
    pending = "pending"
    running = "running"
    done = "done"
    failed = "failed"
