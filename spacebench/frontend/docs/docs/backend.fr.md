# Backend

Le backend est la couche d'orchestration de SpaceBench. Il reçoit les fichiers depuis le frontend, les valide immédiatement, stocke les métadonnées de validation dans PostgreSQL, crée les analyses et lance le moteur POD.

La prévalidation appartient au backend, pas au moteur POD. Elle a lieu avant le démarrage d'une analyse et avant le parsing scientifique des fichiers par `georinex`.

---

## Responsabilités

| Responsabilité | Implémentation |
|----------------|----------------|
| Upload de fichiers | `backend/app/routers/files/files.py` |
| Prévalidation par format | `backend/app/validators/upload` |
| Persistance des métadonnées de validation | `UploadedFile.validation_metadata` |
| Création d'analyse | `backend/app/routers/runs/run.py` |
| Regroupement des fichiers par analyse | `organize_run_files()` |
| Lancement du moteur POD | `LaunchRunService` |
| API des logs d'analyse | `GET /api/runs/{run_id}/logs` |

---

## Prévalidation À L'upload

Lorsqu'un fichier est téléversé via `POST /api/files/upload`, le backend :

1. vérifie l'extension ;
2. stocke temporairement le fichier ;
3. sélectionne le validateur correspondant ;
4. valide le contenu du fichier ;
5. supprime le fichier et retourne HTTP `422` si la validation échoue ;
6. stocke l'enregistrement du fichier et ses métadonnées de validation si la validation réussit.

Les validateurs suivent un modèle commun via `FileValidator` :

```python
class FileValidator(ABC):
    ext: str
    file_type: FileType

    def read_ascii_lines(...)
    def send_error(...)
    def parse_epoch(...)

    @abstractmethod
    def validate(...)
```

Les validateurs concrets sont sélectionnés via une stratégie par type de fichier :

| Type de fichier | Extension | Validateur |
|-----------------|-----------|------------|
| Observations RINEX | `.rnx` | `RnxValidator` |
| Fichier d'orbite SP3 | `.sp3` | `Sp3Validator` |
| Fichier d'horloge RINEX | `.clk_30s` | `ClkValidator` |
| Estimateur personnalisé | `.py` | `PythonValidator` |

---

## Sorties Des Validateurs

Chaque validateur retourne :

```python
class FileValidationResult(BaseModel):
    valid: bool
    issues: list[FileValidationError]
    metadata: dict
```

Les erreurs de validation sont structurées avec un code, un message et un numéro de ligne. Cela permet de fournir un retour déterministe côté frontend.

### Validateur RINEX

`RnxValidator` vérifie actuellement :

| Vérification | Objectif |
|--------------|----------|
| décodage ASCII et contenu non vide | rejeter les fichiers illisibles |
| en-tête `RINEX VERSION / TYPE` | confirmer le format RINEX |
| version RINEX 2 | format d'observation actuellement supporté |
| type `OBSERVATION DATA` | rejeter les fichiers RINEX non observation |
| ligne `# / TYPES OF OBSERV` | confirmer la structure des observations |
| `END OF HEADER` | confirmer l'intégrité de l'en-tête |
| `TIME OF FIRST OBS` | extraire l'époque de début |
| première époque d'observation | confirmer la présence de données |
| cohérence époque/en-tête | vérifier que la première époque correspond à l'en-tête |
| marqueur d'époque et nombre de satellites | rejeter une première époque non supportée |
| premier bloc d'observation satellite | confirmer la présence des champs d'observation |

Les métadonnées stockées incluent la version RINEX, la ligne de fin d'en-tête, l'époque de début, le nombre d'observables, l'index de la première époque, le nombre de satellites de la première époque, le nombre de lignes de continuation et le marqueur d'époque.

### Validateur SP3

`Sp3Validator` vérifie actuellement :

| Vérification | Objectif |
|--------------|----------|
| décodage ASCII et contenu non vide | rejeter les fichiers illisibles |
| version SP3 `#a` à `#d` | confirmer une famille SP3 supportée |
| mode `P` ou `V` | confirmer position seule ou position/vitesse |
| époque de début dans l'en-tête | extraire la métadonnée temporelle |
| nombre d'époques | rejeter les produits orbitaux vides |
| liste de satellites | confirmer la présence d'au moins un satellite |
| première époque | confirmer la présence de la section de données |
| enregistrements position et vitesse | vérifier la cohérence avec le mode `P` ou `V` |
| marqueur `EOF` | confirmer la fermeture du fichier |
| cohérence en-tête/données | détecter les en-têtes incohérents |

Les métadonnées stockées incluent la version, le mode, l'époque de début, le nombre d'époques, les identifiants satellite, l'index de la première époque, le nombre d'enregistrements de position et le nombre d'enregistrements de vitesse.

### Validateur CLK

`ClkValidator` vérifie actuellement :

| Vérification | Objectif |
|--------------|----------|
| décodage ASCII et contenu non vide | rejeter les fichiers illisibles |
| version RINEX 3 | format d'horloge actuellement supporté |
| type de fichier horloge `C` | rejeter les fichiers RINEX non horloge |
| `END OF HEADER` | confirmer l'intégrité de l'en-tête |
| premier enregistrement `AS` | confirmer la présence d'horloges satellite |
| timestamp du premier `AS` | extraire la métadonnée de début des horloges |

Les métadonnées stockées incluent la version, la ligne de fin d'en-tête, l'index du premier `AS` et son timestamp.

### Validateur D'estimateur Python

`PythonValidator` parse les estimateurs personnalisés avec `ast`.

Il vérifie :

| Vérification | Objectif |
|--------------|----------|
| décodage UTF-8 et contenu non vide | rejeter les fichiers Python illisibles |
| validité syntaxique | rejeter les fichiers non parsables |
| classe `CustomEstimator` | imposer le point d'extension attendu |
| héritage de `BaseEstimator` | imposer l'interface d'estimateur |
| méthode `estimate()` | confirmer le point d'entrée d'estimation |
| imports interdits | bloquer `os`, `sys`, `subprocess`, `socket` |
| appels interdits | bloquer `eval`, `exec`, `compile`, `__import__`, `open`, `input` |

Cette prévalidation réduit les risques évidents, mais ne constitue pas une sandbox complète.

---

## Création D'analyse Et Lancement Du Moteur

Lorsque le frontend crée une analyse via `POST /api/runs`, le backend :

1. crée l'enregistrement `Run` en base ;
2. relie les fichiers RSO sélectionnés via `RunRsoFile` ;
3. déplace les fichiers uploadés dans un dossier propre à l'analyse ;
4. charge les métadonnées de validation de chaque fichier ;
5. construit le payload du moteur POD ;
6. lance le moteur de manière asynchrone.

Le payload envoyé au moteur POD contient les chemins de fichiers et les métadonnées de validation :

```python
metadata = {
    "rinex": rinex_file.validation_metadata,
    "gnss_sp3": gnss_sp3_file.validation_metadata,
    "rso_sp3": rso_metadata,
    "clk": clk_file.validation_metadata,
}
```

La configuration est aussi envoyée au moteur POD.

```python
config = {
    "rinex_file_id": run.rinex_file_id,
    "gnss_sp3_file_id": run.gnss_sp3_file_id,
    "gnss_clk_file_id": run.gnss_clk_file_id,
    "rso_file_ids": rso_file_ids,
    "rinex_path": rinex_file.stored_path,
    "gnss_sp3_path": gnss_sp3_file.stored_path,
    "gnss_clk_path": clk_file.stored_path,
    "rso_sp3_paths": rso_paths,
    "orbital_model": run.orbital_model,
    "estimator_type": run.estimator_type,
    "estimator_file_id": estimator_file_id,
    "estimator_path": estimator_path,
    "max_iteration": run.max_iteration,
    "tolerance": run.tolerance
}
```
Le moteur effectue ensuite une validation croisée avec ces métadonnées avant de parser le contenu scientifique.


---

## Pourquoi Cette Séparation

Garder la prévalidation dans le backend présente trois avantages :

| Avantage | Explication |
|----------|-------------|
| Retour immédiat dans le frontend | Les fichiers invalides échouent à l'upload, avant le lancement d'une analyse |
| Moteur plus clair | Le moteur POD peut se concentrer sur le traitement scientifique |
| Meilleure traçabilité | Les métadonnées par fichier sont stockées une seule fois et réutilisées lors de la création des analyses |

Le moteur POD doit tout de même valider la cohérence d'une analyse, car des fichiers individuellement valides peuvent rester incompatibles scientifiquement.
