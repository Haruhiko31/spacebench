# Liste des erreurs de validation

Cette page référence les codes d'erreur retournés par le système de validation des fichiers téléversés dans SpaceBench.

Chaque erreur contient :

| Champ | Description |
|------|-------------|
| `code` | Identifiant stable de l'erreur |
| `message` | Description lisible de l'erreur |
| `line` | Ligne concernée dans le fichier, lorsque disponible. `0` signifie que l'erreur est globale ou non localisée. |

---

## Erreurs communes à tous les fichiers

Ces erreurs peuvent apparaître pour tous les types de fichiers supportés.

| Code | Fichier(s) | Cause | Action recommandée |
|---|---|---|---|
| `FILE_EMPTY` | Tous | Le fichier est vide. | Vérifier que le fichier sélectionné contient bien des données. |
| `COMMON_FILE_DECODE_ERROR` | Tous | Le fichier ne peut pas être décodé. Les fichiers SP3, RINEX et CLK sont attendus en ASCII ; les plugins Python sont attendus en UTF-8. | Vérifier l'encodage du fichier ou régénérer le fichier depuis la source originale. |

---

## Erreurs SP3

Ces erreurs concernent les fichiers `.sp3`, utilisés pour les orbites précises GNSS ou les orbites de référence RSO.

| Code | Cause | Action recommandée |
|---|---|---|
| `SP3_FILE_TOO_SHORT` | Le fichier contient trop peu de lignes pour être un fichier SP3 valide. | Vérifier que le fichier SP3 n'est pas tronqué. |
| `SP3_FILE_HEADER_ERROR` | La première ligne d'en-tête SP3 est incomplète ou mal formée. | Vérifier la première ligne du fichier, par exemple `#dP...` ou `#dV...`. |
| `SP3_FILE_VERSION_ERROR` | La version SP3 n'est pas reconnue. Les versions acceptées sont `#a`, `#b`, `#c`, `#d`. | Fournir un fichier SP3 compatible. |
| `SP3_FILE_MODE_ERROR` | Le mode SP3 est invalide ou le contenu ne correspond pas au mode déclaré. | Vérifier le caractère de mode `P` ou `V` dans la première ligne, ainsi que les lignes de données `P` et `V`. |
| `SP3_FILE_START_EPOCH_ERROR` | L'époque de départ déclarée dans l'en-tête n'est pas lisible. | Vérifier les champs date/heure de la première ligne SP3. |
| `SP3_FILE_EPOCH_COUNT_ERROR` | Le nombre d'époques est absent, invalide ou nul. | Vérifier le champ du nombre d'époques dans l'en-tête SP3. |
| `SP3_FILE_NUMBER_OF_SATS_ERROR` | Aucun satellite n'a été trouvé dans les lignes `+` de l'en-tête. | Vérifier que la liste des satellites est présente dans l'en-tête SP3. |
| `SP3_FILE_FIRST_EPOCH_ERROR` | Aucune première époque valide n'a été trouvée. | Vérifier la présence d'une ligne d'époque commençant par `*`. |
| `SP3_FILE_DATA_ERROR` | Une époque existe, mais aucune ligne de données ne suit. | Vérifier que le fichier contient des lignes `P...` ou `V...` après les époques. |
| `SP3_FILE_MISSING_POSITION_ERROR` | Aucun enregistrement de position `P` n'a été trouvé. | Vérifier que le fichier contient des lignes de position, par exemple `PG01 ...` ou `PL06 ...`. |
| `SP3_FILE_MISSING_VELOCITY_ERROR` | Le fichier est déclaré en mode `V`, mais aucune ligne de vitesse `V` n'a été trouvée. | Vérifier que les lignes de vitesse sont présentes si le mode déclaré est `V`. |
| `SP3_FILE_EOF_ERROR` | Le fichier ne se termine pas par `EOF`. | Vérifier que le fichier SP3 n'est pas tronqué. |
| `SP3_FILE_EPOCH_ERROR` | La première époque de données ne correspond pas à l'époque de départ déclarée dans l'en-tête. | Vérifier la cohérence temporelle entre la première ligne d'en-tête et la première ligne `*`. |

---

## Erreurs RINEX Observation

Ces erreurs concernent les fichiers `.rnx`, attendus comme fichiers d'observations RINEX 2.

| Code | Cause | Action recommandée |
|---|---|---|
| `RINEX_FILE_TOO_SHORT` | Le fichier est trop court pour être un fichier RINEX valide. | Vérifier que le fichier n'est pas tronqué. |
| `RINEX_FILE_HEADER_ERROR` | La ligne `RINEX VERSION / TYPE` est absente, ou l'en-tête ne contient pas `END OF HEADER` dans la limite attendue. | Vérifier que l'en-tête RINEX est complet. |
| `RINEX_FILE_VERSION_ERROR` | La version RINEX est absente, invalide ou non supportée. SpaceBench attend actuellement RINEX 2 pour les observations mission. | Fournir un fichier d'observations RINEX 2 compatible. |
| `RINEX_FILE_TYPE_ERROR` | Le fichier n'est pas déclaré comme `OBSERVATION DATA`. | Vérifier que le fichier est bien un fichier d'observations et non un fichier navigation, horloge ou météo. |
| `RINEX_FILE_OBSERVATION_TYPE_ERROR` | La ligne `# / TYPES OF OBSERV` est absente. | Vérifier que l'en-tête RINEX déclare les types d'observation. |
| `RINEX_FILE_OBSERVATION_COUNT_ERROR` | Le nombre de types d'observation est absent, invalide ou nul. | Vérifier la ligne `# / TYPES OF OBSERV`, par exemple `9 L1 L2 C1 ...`. |
| `RINEX_FILE_START_EPOCH_ERROR` | La ligne `TIME OF FIRST OBS` est absente ou invalide. | Vérifier la date de première observation dans l'en-tête. |
| `RINEX_FILE_FIRST_EPOCH_ERROR` | Aucune première époque d'observation valide n'a été trouvée après l'en-tête. | Vérifier que la section de données commence correctement après `END OF HEADER`. |
| `RINEX_FILE_EPOCH_ERROR` | La première époque de données ne correspond pas à `TIME OF FIRST OBS`. | Vérifier la cohérence temporelle entre l'en-tête et la première époque. |
| `RINEX_FILE_EPOCH_FLAG_ERROR` | Le marqueur de la première époque est invalide ou non supporté. | Vérifier le champ `epoch flag`. Les valeurs normales attendues sont généralement `0` ou `1`. |
| `RINEX_FILE_START_EPOCH_SAT_COUNT_ERROR` | Le nombre de satellites dans la première époque est absent, invalide ou nul. | Vérifier la ligne de première époque. |
| `RINEX_FILE_FIRST_DATA_ERROR` | Les données d'observation après la première époque sont absentes ou incomplètes. | Vérifier que chaque satellite dispose d'un bloc d'observations correspondant aux types déclarés. |

---

## Erreurs RINEX CLK

Ces erreurs concernent les fichiers `.clk_30s`, attendus comme fichiers d'horloges RINEX Clock v3.

| Code | Cause | Action recommandée |
|---|---|---|
| `CLK_FILE_HEADER_ERROR` | La ligne `RINEX VERSION / TYPE` est absente, ou l'en-tête ne se termine pas correctement par `END OF HEADER`. | Vérifier que l'en-tête CLK est complet et que le fichier n'est pas tronqué ou mal formé. |
| `CLK_FILE_VERSION_ERROR` | La version RINEX Clock est absente, invalide ou non supportée. SpaceBench attend RINEX v3. | Fournir un fichier CLK RINEX 3 compatible. |
| `CLK_FILE_TYPE_ERROR` | Le type de fichier n'est pas `C`, ou le champ type est absent. | Vérifier que le fichier est bien un fichier d'horloges RINEX. |
| `CLK_FILE_DATA_ERROR` | Aucun enregistrement `AS` n'a été trouvé. | Fournir un fichier contenant des horloges satellites `AS`, nécessaires au traitement POD. |
| `CLK_FILE_TIMESTAMP_ERROR` | Le timestamp du premier enregistrement `AS` est invalide. | Vérifier la première ligne `AS`, par exemple `AS G02 2010 07 19 00 00 0.000000 ...`. |

---

## Erreurs plugin Python

Ces erreurs concernent les fichiers `.py` utilisés comme estimateurs personnalisés.

| Code | Cause | Action recommandée |
|---|---|---|
| `PY_FILE_SYNTAX_ERROR` | Le fichier Python contient une erreur de syntaxe. | Corriger la syntaxe du fichier `.py`. |
| `PY_FILE_CUSTOM_ESTIMATOR_ERROR` | Aucune classe `CustomEstimator` n'a été trouvée. | Définir une classe nommée exactement `CustomEstimator`. |
| `PY_FILE_BASE_ESTIMATOR_ERROR` | `CustomEstimator` n'hérite pas de `BaseEstimator`. | Déclarer `class CustomEstimator(BaseEstimator):`. |
| `PY_FILE_ESTIMATE_METHOD_ERROR` | La méthode `estimate` est absente. | Ajouter une méthode `estimate(...)` dans `CustomEstimator`. |
| `PY_FILE_FORBIDDEN_IMPORT` | Le fichier importe un module interdit, par exemple `os`, `sys`, `subprocess` ou `socket`. | Supprimer les imports dangereux. |
| `PY_FILE_FORBIDDEN_CALL` | Le fichier appelle une fonction interdite, par exemple `eval`, `exec`, `compile`, `__import__`, `open` ou `input`. | Supprimer les appels dangereux. |

---

## Notes sur la validation

La validation effectuée par SpaceBench est une pré-validation structurelle. Elle vérifie que les fichiers sont lisibles, cohérents avec le format attendu, et suffisamment complets pour être transmis au pipeline POD.

Elle ne remplace pas une analyse scientifique complète du contenu. Par exemple, un fichier SP3 peut être structurellement valide mais contenir des produits orbitaux de qualité insuffisante ou incompatibles temporellement avec une mission donnée.

Pour les plugins Python personnalisés, la validation AST permet de vérifier la structure du code sans l'exécuter. Elle ne constitue pas une sandbox de sécurité complète. L'exécution d'un plugin personnalisé doit être isolée dans un environnement contrôlé.
