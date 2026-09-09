'''
    Claude Code CLI wrote this (Sonnet 4.6)
'''

import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, select, delete
from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.models.pod import (
    Run,
    UploadedFile,
    RunRsoFile,
    FileType,
    OrbitalModel,
    EstimatorType,
    RunStatus,
)
# Set to 1 for the default 20 rows, higher to stress-test the UI (e.g. 100 → 2000 rows).
SEED_MULTIPLIER = 10

# Reset before inserting new rows.
DROP_BEFORE = 1

# When 1: skip seeding if the DB already has >= MULTIPLIER * base rows.
# When 0: always insert (ON CONFLICT DO NOTHING still prevents true duplicates).
SEED_IDEMPOTENT = 1

SEED_FILES = [
    {
        "id": "file-rinex-0001",
        "original_name": "CHAMP_2010_246.rnx",
        "stored_path": "./seed/CHAMP_2010_246.rnx",
        "file_type": FileType.rinex,
        "uploaded_at": datetime(2025, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        "validation_metadata": {
            "seed": True,
            "kind": "rinex",
            "start_epoch": "2010-09-03T00:00:00",
            "epoch_count": 8640,
        },
    },
    {
        "id": "file-gnss-sp3-0001",
        "original_name": "igs_2010_246.sp3",
        "stored_path": "./seed/igs_2010_246.sp3",
        "file_type": FileType.sp3,
        "uploaded_at": datetime(2025, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        "validation_metadata": {
            "seed": True,
            "kind": "gnss_sp3",
            "version": 3,
        },
    },
    {
        "id": "file-gnss-clk-0001",
        "original_name": "igs_2010_246.clk",
        "stored_path": "./seed/igs_2010_246.clk",
        "file_type": FileType.clock,
        "uploaded_at": datetime(2025, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        "validation_metadata": {
            "seed": True,
            "kind": "gnss_clk",
        },
    },
    {
        "id": "file-rso-sp3-0001",
        "original_name": "champ_2010_246_reference.sp3",
        "stored_path": "./seed/champ_2010_246_reference.sp3",
        "file_type": FileType.sp3,
        "uploaded_at": datetime(2025, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        "validation_metadata": {
            "seed": True,
            "kind": "rso_sp3",
        },
    },
    {
        "id": "file-rso-sp3-0002",
        "original_name": "champ_2010_246_reference_alt.sp3",
        "stored_path": "./seed/champ_2010_246_reference_alt.sp3",
        "file_type": FileType.sp3,
        "uploaded_at": datetime(2025, 1, 5, 10, 0, 0, tzinfo=timezone.utc),
        "validation_metadata": {
            "seed": True,
            "kind": "rso_sp3",
        },
    },
]

SEED_RUN_RSO_FILES = [
    {
        "run_id": "seed-0001-0000-0000-000000000001",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000001",
        "file_id": "file-rso-sp3-0002",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000002",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000003",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000004",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000005",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000006",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000007",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000008",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000009",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000010",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000011",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000012",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000013",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000014",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000015",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000016",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000017",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000018",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000019",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000020",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000021",
        "file_id": "file-rso-sp3-0001",
    },
    {
        "run_id": "seed-0001-0000-0000-000000000022",
        "file_id": "file-rso-sp3-0001",
    },
]

SEED_RUNS = [
    {
        "id":             "seed-0001-0000-0000-000000000001",
        "name":           "CHAMP - Jour 246 - Cinématique LS",
        "mission_name":   "CHAMP",
        "mission_year":   2002,
        "mission_day":    246,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  6,
        "tolerance":      0.120,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         29500,  "rms_radial": 11800, "rms_along": 22715, "rms_cross": 14750,
        "created_at":     datetime(2025, 1, 5, 10, 12, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 29500 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000002",
        "name":           "CHAMP - Jour 246 - Cinématique Kalman",
        "mission_name":   "CHAMP",
        "mission_year":   2002,
        "mission_day":    246,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  3,
        "tolerance":      0.015,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         26200,  "rms_radial": 10480, "rms_along": 20174, "rms_cross": 13100,
        "created_at":     datetime(2025, 1, 6, 14, 33, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 26200 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000003",
        "name":           "CHAMP - Jour 200 - Cinématique LS",
        "mission_name":   "CHAMP",
        "mission_year":   2002,
        "mission_day":    200,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  6,
        "tolerance":      0.120,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         31000,  "rms_radial": 12400, "rms_along": 23870, "rms_cross": 15500,
        "created_at":     datetime(2025, 1, 8, 9, 5, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 31000 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000004",
        "name":           "GRACE-FO - 2019-03-15 - Cinématique LS",
        "mission_name":   "GRACE-FO",
        "mission_year":   2019,
        "mission_day":    74,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  5,
        "tolerance":      0.050,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         23400,  "rms_radial": 7020, "rms_along": 18720, "rms_cross": 12170,
        "created_at":     datetime(2025, 1, 12, 16, 47, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 23400 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000005",
        "name":           "GRACE-FO - 2019-03-15 - Kalman",
        "mission_name":   "GRACE-FO",
        "mission_year":   2019,
        "mission_day":    74,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  3,
        "tolerance":      0.008,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         21000,  "rms_radial": 6300, "rms_along": 16800, "rms_cross": 10920,
        "created_at":     datetime(2025, 1, 13, 11, 22, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 21000 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000006",
        "name":           "Sentinel-6 - 2021-06-01 - Cinématique LS",
        "mission_name":   "Sentinel-6",
        "mission_year":   2021,
        "mission_day":    152,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  4,
        "tolerance":      0.025,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         18800,  "rms_radial": 6390, "rms_along": 15040, "rms_cross": 9400,
        "created_at":     datetime(2025, 1, 20, 8, 14, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 18800 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000007",
        "name":           "SWARM-A - 2016-11-10 - Cinématique LS",
        "mission_name":   "SWARM-A",
        "mission_year":   2016,
        "mission_day":    315,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  5,
        "tolerance":      0.080,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         26500,  "rms_radial": 9540, "rms_along": 20405, "rms_cross": 14045,
        "created_at":     datetime(2025, 1, 25, 13, 55, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 26500 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000008",
        "name":           "SWARM-B - 2016-11-10 - Cinématique LS",
        "mission_name":   "SWARM-B",
        "mission_year":   2016,
        "mission_day":    315,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  5,
        "tolerance":      0.080,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         27200,  "rms_radial": 9790, "rms_along": 20945, "rms_cross": 14415,
        "created_at":     datetime(2025, 2, 1, 10, 30, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 27200 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000009",
        "name":           "GOCE - 2011-09-20 - Cinématique LS",
        "mission_name":   "GOCE",
        "mission_year":   2011,
        "mission_day":    263,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  8,
        "tolerance":      0.150,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         34500,  "rms_radial": 14835, "rms_along": 26220, "rms_cross": 16905,
        "created_at":     datetime(2025, 2, 5, 15, 18, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 34500 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000010",
        "name":           "Jason-3 - 2022-04-12 - Cinématique LS",
        "mission_name":   "Jason-3",
        "mission_year":   2022,
        "mission_day":    102,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  4,
        "tolerance":      0.035,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         20500,  "rms_radial": 7585, "rms_along": 16810, "rms_cross": 9020,
        "created_at":     datetime(2025, 2, 10, 9, 42, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 20500 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000011",
        "name":           "CHAMP - Jour 246 - Dynamique LS",
        "mission_name":   "CHAMP",
        "mission_year":   2002,
        "mission_day":    246,
        "orbital_model":  OrbitalModel.dynamic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  7,
        "tolerance":      0.100,
        "status":         RunStatus.failed,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         None,  "rms_radial": None, "rms_along": None, "rms_cross": None,
        "created_at":     datetime(2025, 2, 14, 17, 5, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé\n[ERROR] Modèle dynamique non implémenté\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000012",
        "name":           "GRACE-FO - 2020-01-08 - Réduit-Dynamique",
        "mission_name":   "GRACE-FO",
        "mission_year":   2020,
        "mission_day":    8,
        "orbital_model":  OrbitalModel.reduced_dynamic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  4,
        "tolerance":      0.010,
        "status":         RunStatus.failed,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         None,  "rms_radial": None, "rms_along": None, "rms_cross": None,
        "created_at":     datetime(2025, 2, 18, 12, 0, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[ERROR] Modèle réduit-dynamique non implémenté\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000013",
        "name":           "Sentinel-6 - 2022-09-30 - Kalman",
        "mission_name":   "Sentinel-6",
        "mission_year":   2022,
        "mission_day":    273,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  2,
        "tolerance":      0.003,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         18000,  "rms_radial": 6120, "rms_along": 14400, "rms_cross": 9000,
        "created_at":     datetime(2025, 2, 22, 14, 11, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 18000 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000014",
        "name":           "SWARM-C - 2017-03-22 - Cinématique LS",
        "mission_name":   "SWARM-C",
        "mission_year":   2017,
        "mission_day":    81,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  5,
        "tolerance":      0.080,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         25800,  "rms_radial": 9290, "rms_along": 19865, "rms_cross": 13675,
        "created_at":     datetime(2025, 3, 1, 8, 30, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 25800 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000015",
        "name":           "GOCE - 2012-05-15 - Cinématique Kalman",
        "mission_name":   "GOCE",
        "mission_year":   2012,
        "mission_day":    136,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  4,
        "tolerance":      0.020,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         32000,  "rms_radial": 13760, "rms_along": 24320, "rms_cross": 15680,
        "created_at":     datetime(2025, 3, 6, 11, 0, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 32000 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000016",
        "name":           "CHAMP - Jour 200 - Kalman",
        "mission_name":   "CHAMP",
        "mission_year":   2002,
        "mission_day":    200,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  3,
        "tolerance":      0.015,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         28000,  "rms_radial": 11200, "rms_along": 21560, "rms_cross": 14000,
        "created_at":     datetime(2025, 3, 10, 16, 44, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 28000 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000017",
        "name":           "Jason-3 - 2023-11-01 - Cinématique LS",
        "mission_name":   "Jason-3",
        "mission_year":   2023,
        "mission_day":    305,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  4,
        "tolerance":      0.035,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         19800,  "rms_radial": 7325, "rms_along": 16235, "rms_cross": 8710,
        "created_at":     datetime(2025, 3, 14, 9, 20, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 19800 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000018",
        "name":           "GRACE-FO - 2021-07-20 - Plugin custom",
        "mission_name":   "GRACE-FO",
        "mission_year":   2021,
        "mission_day":    201,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.custom,
        "max_iteration":  5,
        "tolerance":      0.040,
        "status":         RunStatus.failed,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         None,  "rms_radial": None, "rms_along": None, "rms_cross": None,
        "created_at":     datetime(2025, 3, 18, 13, 55, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé\n[ERROR] Plugin custom : exception non gérée\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000019",
        "name":           "Sentinel-6 - 2023-02-14 - Cinématique LS",
        "mission_name":   "Sentinel-6",
        "mission_year":   2023,
        "mission_day":    45,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  4,
        "tolerance":      0.025,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         19200,  "rms_radial": 6530, "rms_along": 15360, "rms_cross": 9600,
        "created_at":     datetime(2025, 3, 22, 10, 10, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 19200 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000020",
        "name":           "CHAMP - Jour 246 - Plugin custom",
        "mission_name":   "CHAMP",
        "mission_year":   2002,
        "mission_day":    246,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.custom,
        "max_iteration":  6,
        "tolerance":      0.080,
        "status":         RunStatus.done,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         29000,  "rms_radial": 11600, "rms_along": 22330, "rms_cross": 14500,
        "created_at":     datetime(2025, 3, 28, 15, 0, 0, tzinfo=timezone.utc),
        "logs":           "[INFO] Chargement des fichiers\n[INFO] Parsing RINEX terminé - 8640 époques\n[INFO] Pipeline démarré\n[RESULT] RMS 3D : 29000 cm\n",
    },
    {
        "id":             "seed-0001-0000-0000-000000000021",
        "name":           "SWARM-A - 2017-03-22 - Cinématique LS",
        "mission_name":   "SWARM-A",
        "mission_year":   2017,
        "mission_day":    81,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.least_squares,
        "max_iteration":  5,
        "tolerance":      0.080,
        "status":         RunStatus.pending,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         None,  "rms_radial": None, "rms_along": None, "rms_cross": None,
        "created_at":     datetime(2025, 4, 1, 8, 0, 0, tzinfo=timezone.utc),
        "logs":           "",
    },
    {
        "id":             "seed-0001-0000-0000-000000000022",
        "name":           "GRACE-FO - 2020-01-08 - Kalman",
        "mission_name":   "GRACE-FO",
        "mission_year":   2020,
        "mission_day":    8,
        "orbital_model":  OrbitalModel.kinematic,
        "estimator_type": EstimatorType.kalman,
        "max_iteration":  3,
        "tolerance":      0.008,
        "status":         RunStatus.pending,
        "rinex_file_id": "file-rinex-0001",
        "gnss_sp3_file_id": "file-gnss-sp3-0001",
        "gnss_clk_file_id": "file-gnss-clk-0001",
        "estimator_file_id": None,
        "rms_3d":         None,  "rms_radial": None, "rms_along": None, "rms_cross": None,
        "created_at":     datetime(2025, 4, 2, 11, 30, 0, tzinfo=timezone.utc),
        "logs":           "",
    },
]


def _make_rows() -> list[dict]:
    rows = []
    for copy in range(SEED_MULTIPLIER):
        for base in SEED_RUNS:
            if copy == 0:
                row = dict(base)
            else:
                # Deterministic UUID derived from original id + copy index
                new_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{base['id']}-{copy}"))
                # Slightly vary RMS values so each copy looks different on the chart
                factor = 1 + (copy % 10) * 0.08
                row = {
                    **base,
                    "id":         new_id,
                    "name":       f"{base['name']} #{copy + 1}",
                    "created_at": base["created_at"] + timedelta(days=copy * 7),
                    "rms_3d":     round(base["rms_3d"]     * factor, 2) if base["rms_3d"]     else None,
                    "rms_radial": round(base["rms_radial"] * factor, 2) if base["rms_radial"] else None,
                    "rms_along":  round(base["rms_along"]  * factor, 2) if base["rms_along"]  else None,
                    "rms_cross":  round(base["rms_cross"]  * factor, 2) if base["rms_cross"]  else None,
                }
            rows.append(row)
    return rows


async def seed_default_runs() -> None:

    expected = SEED_MULTIPLIER * len(SEED_RUNS)

    if SEED_IDEMPOTENT:
        async with SessionLocal() as session:
            count = (await session.execute(select(func.count()).select_from(Run))).scalar_one()

        if count >= expected:
            print(f"[skip] Seed: {count} rows already present (expected {expected})")
            return

    rows = _make_rows()

    async with SessionLocal() as session:
        # 1. Insert files first because runs reference files.
        for data in SEED_FILES:
            stmt = (
                insert(UploadedFile)
                .values(**data)
                .on_conflict_do_nothing(index_elements=["id"])
            )
            await session.execute(stmt)

        # 2. Insert runs.
        for data in rows:
            stmt = (
                insert(Run)
                .values(**data)
                .on_conflict_do_nothing(index_elements=["id"])
            )
            await session.execute(stmt)

        # 3. Insert run -> RSO file links.
        for data in SEED_RUN_RSO_FILES:
            stmt = (
                insert(RunRsoFile)
                .values(**data)
                .on_conflict_do_nothing(index_elements=["run_id", "file_id"])
            )
            await session.execute(stmt)

        await session.commit()

    print(f"[ok] Seed: {len(rows)} runs inserted ({SEED_MULTIPLIER}× {len(SEED_RUNS)} base rows)")