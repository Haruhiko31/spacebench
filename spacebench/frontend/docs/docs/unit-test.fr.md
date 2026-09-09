# Tests unitaires

Les tests unitaires sont organisés par composant applicatif. Les tableaux suivants présentent les différents tests disponibles, l'endpoint concerné lorsque celui-ci existe, leur objectif, ainsi que le comportement attendu.

---

## Tests unitaires Backend

### Santé et documentation

| Test | Endpoint | Description | Résultat attendu |
|------|----------|-------------|------------------|
| `test_health_returns_200` | `/health` | Vérifie que l'endpoint de santé du backend est joignable. | HTTP 200 |
| `test_health_response_body` | `/health` | Vérifie que la réponse contient un champ `status` avec la valeur `ok`. | `status = ok` |
| `test_redoc_returns_200` | `/api/redoc` | Vérifie que la documentation ReDoc est accessible. | HTTP 200 |
| `test_swagger_returns_200` | `/api/docs` | Vérifie que la documentation Swagger est accessible. | HTTP 200 |

### Gestion des fichiers

| Test | Endpoint | Description | Résultat attendu |
|------|----------|-------------|------------------|
| `test_upload_valid_file` | `/api/files/upload` | Vérifie qu'un fichier valide peut être téléversé et que la réponse contient un identifiant ainsi que le nom original du fichier. | HTTP 201 |
| `test_upload_bad_extension` | `/api/files/upload` | Vérifie qu'un fichier avec une extension non supportée est rejeté. | HTTP 400 |
| `test_upload_invalid_content` | `/api/files/upload` | Vérifie qu'un fichier dont le contenu est invalide est rejeté, même si son extension est correcte. | HTTP 422 |
| `test_download_existing_file` | `/api/files/{id}/download` | Vérifie qu'un fichier existant peut être téléchargé à partir de son identifiant. | HTTP 200 |
| `test_download_non_existing_file` | `/api/files/{id}/download` | Vérifie que la tentative de téléchargement d'un fichier inexistant retourne une erreur. | HTTP 404 |
| `test_bulk_download_existing` | `/api/files/bulk/download` | Vérifie que le téléchargement groupé fonctionne lorsqu'une liste d'identifiants valides est fournie. | HTTP 200 |
| `test_bulk_download_non_existing` | `/api/files/bulk/download` | Vérifie que le téléchargement groupé échoue lorsqu'un identifiant de fichier inexistant est fourni. | HTTP 404 |
| `test_bulk_download_empty` | `/api/files/bulk/download` | Vérifie qu'une liste vide d'identifiants est refusée lors d'un téléchargement groupé. | HTTP 400 |

### Gestion des exécutions

| Test | Endpoint | Description | Résultat attendu |
|------|----------|-------------|------------------|
| `test_run_valid` | `/api/runs` | Vérifie qu'une exécution valide peut être créée avec les paramètres requis. | HTTP 201 |
| `test_run_invalid` | `/api/runs` | Vérifie qu'une exécution incomplète ou invalide est rejetée par l'API. | HTTP 422 |
| `test_get_run_count` | `/api/runs/count` | Vérifie que le nombre total d'exécutions peut être récupéré. | HTTP 200 |
| `test_get_run_count_filtered_by_statut` | `/api/runs/count?statuses=pending` | Vérifie que le nombre d'exécutions peut être filtré selon le statut. | HTTP 200 |
| `test_get_run_filtered_by_unknown_status` | `/api/runs/count?statuses=unknown_status` | Vérifie qu'un statut inconnu est rejeté lors du comptage des exécutions. | HTTP 422 |
| `test_get_list_runs` | `/api/runs` | Vérifie que la liste des exécutions peut être récupérée. | HTTP 200 |
| `test_get_existing_run` | `/api/runs/{id}` | Vérifie qu'une exécution existante peut être récupérée à partir de son identifiant. | HTTP 200 |
| `test_get_non_existing_run` | `/api/runs/9999999` | Vérifie qu'une erreur est retournée lorsqu'une exécution inexistante est demandée. | HTTP 404 |
| `test_list_runs_with_sort` | `/api/runs?sort_by=name&sort_order=asc&limit=5` | Vérifie que la liste des exécutions peut être triée et limitée. | HTTP 200 |
| `test_list_runs_filtered_by_status` | `/api/runs?statuses=pending` | Vérifie que la liste des exécutions peut être filtrée par statut. | HTTP 200 |
| `test_list_runs_filtered_by_unknown_status` | `/api/runs?statuses=unknown_status` | Vérifie qu'un statut inconnu est rejeté lors du filtrage des exécutions. | HTTP 422 |
| `test_get_run_logs` | `/api/runs/{id}/logs` | Vérifie le comportement de l'API lorsqu'aucun journal d'exécution n'est disponible pour une exécution existante. | HTTP 404 |
| `test_get_run_logs_non_existing` | `/api/runs/9999999/logs` | Vérifie qu'une erreur est retournée lors de la demande des journaux d'une exécution inexistante. | HTTP 404 |

---

## Tests unitaires du moteur POD

### Santé et endpoint

| Test | Endpoint | Description | Résultat attendu |
|------|----------|-------------|------------------|
| `test_health_returns_200` | `/health` | Vérifie que l'endpoint de santé du moteur POD est joignable. | HTTP 200 |
| `test_health_response_body` | `/health` | Vérifie que la réponse du moteur POD contient un champ `status` avec la valeur `ok`. | `status = ok` |
| `test_analysis_returns_200` | `/api/runs?tested=true` | Vérifie qu'une analyse POD peut être lancée avec un payload valide. | HTTP 200 |
| `test_analysis_missing_payload` | `/api/runs?tested=true` | Vérifie qu'une requête d'analyse POD sans payload est rejetée par l'API. | HTTP 422 |

### Initialisation et validation croisée

| Test | Fonction | Description | Résultat attendu |
|------|----------|-------------|------------------|
| `test_init_passes` | `init` | Vérifie que la phase d'initialisation retourne un résultat valide lorsque toutes les métadonnées requises sont fournies. | Résultat non nul |
| `test_init_not_all` | `init` | Vérifie que l'initialisation échoue lorsqu'une métadonnée obligatoire, telle que le fichier d'horloge GNSS, est absente. | `None` |
| `test_init_missing_dict_key` | `init` | Vérifie que l'initialisation échoue lorsqu'une clé obligatoire du dictionnaire de métadonnées est absente. | `None` |
| `test_cross_validate_passes` | `cross_validate` | Vérifie que la validation croisée accepte un jeu de métadonnées cohérent. | `True` |
| `test_cross_validate_small_offset_sp3_ok` | `cross_validate` | Vérifie qu'un décalage temporel acceptable du fichier SP3 GNSS est toléré. | `True` |
| `test_cross_validate_small_offset_clk_ok` | `cross_validate` | Vérifie qu'un décalage temporel acceptable du fichier d'horloge GNSS est toléré. | `True` |
| `test_cross_validate_small_offset_sp3_60s_ok` | `cross_validate` | Vérifie qu'un décalage de 60 secondes du fichier SP3 GNSS reste accepté. | `True` |
| `test_cross_validate_small_offset_clk_60s_ok` | `cross_validate` | Vérifie qu'un décalage de 60 secondes du fichier d'horloge GNSS reste accepté. | `True` |
| `test_cross_validate_small_offset_sp3_nok` | `cross_validate` | Vérifie qu'un décalage supérieur au seuil autorisé pour le fichier SP3 GNSS est rejeté. | `False` |
| `test_cross_validate_small_offset_clk_nok` | `cross_validate` | Vérifie qu'un décalage supérieur au seuil autorisé pour le fichier d'horloge GNSS est rejeté. | `False` |
| `test_cross_validate_rso_earliest_one_arc_ok` | `cross_validate` | Vérifie que la validation accepte une observation RSO couvrant correctement le début de l'arc temporel. | `True` |
| `test_cross_validate_rso_earliest_nok` | `cross_validate` | Vérifie que la validation rejette des observations RSO dont le début est trop tardif. | `False` |
| `test_cross_validate_rso_latest_nok` | `cross_validate` | Vérifie que la validation rejette des observations RSO dont la couverture temporelle ne s'étend pas suffisamment loin. | `False` |
| `test_cross_validate_diff_clk_sp3_nok` | `cross_validate` | Vérifie que la validation échoue lorsque les fichiers SP3 et CLK GNSS présentent un décalage temporel incohérent. | `False` |

### Parsing, interpolation et estimation

| Test | Fonction | Description | Résultat attendu |
|------|----------|-------------|------------------|
| `test_parse_clk_reads_sats` | `parse_clk` | Vérifie que le fichier d'horloge GNSS est correctement lu et que les satellites attendus sont détectés. | Satellites présents |
| `test_parse_clk_correct_bias` | `parse_clk` | Vérifie que les biais d'horloge extraits du fichier CLK correspondent aux valeurs attendues. | Valeurs correctes |
| `test_parse_clk_skip_AR` | `parse_clk` | Vérifie que les entrées de type non satellite, telles que les enregistrements AR, sont ignorées lors du parsing. | Entrée ignorée |
| `test_interpolate_clk_mid` | `interpolate_clk` | Vérifie que l'interpolation d'horloge retourne une valeur intermédiaire correcte entre deux époques connues. | Valeur interpolée |
| `test_interpolate_clk_known_epoch` | `interpolate_clk` | Vérifie que l'interpolation retourne directement la valeur connue lorsqu'une époque exacte est demandée. | Valeur exacte |
| `test_interpolate_sp3_skips_missing_sv_value` | `interpolate_sp3` | Vérifie que l'interpolation SP3 ignore un satellite lorsqu'un nombre insuffisant de points est disponible. | Satellite ignoré |
| `test_get_existing_estimator` | `get_estimator` | Vérifie qu'un estimateur existant est correctement résolu à partir de son identifiant. | Estimateur retourné |
| `test_get_non_existing_estimator` | `get_estimator` | Vérifie qu'une erreur est levée lorsqu'un estimateur inconnu est demandé. | `ValueError` |
| `test_get_rso_epoch_data_passed` | `get_rso_epoch_data` | Vérifie que les coordonnées RSO sont correctement récupérées pour une époque existante. | Coordonnées RSO |
| `test_get_rso_epoch_data_unknown` | `get_rso_epoch_data` | Vérifie qu'aucune donnée n'est retournée lorsqu'une époque RSO inexistante est demandée. | `None` |
| `test_initial_rso_state_passed` | `get_initial_RSO_state` | Vérifie que l'état initial du RSO est correctement construit à partir d'une époque existante. | Vecteur d'état |
| `test_initial_rso_state_missing_epoch` | `get_initial_RSO_state` | Vérifie qu'une erreur est levée lorsqu'une époque inexistante est utilisée pour construire l'état initial du RSO. | `ValueError` |