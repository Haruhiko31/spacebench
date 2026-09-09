# Démarrage rapide

## 1. Prérequis

Assurez-vous d'avoir les éléments suivants installés :

- **Docker** (version 24 ou supérieure) et **Docker Compose** — requis pour la méthode recommandée
- **Node.js**, **Python 3.10+** et **PostgreSQL 16** — uniquement si vous démarrez sans Docker (voir [§ 3a](#3a-sans-docker-windows-uniquement-iteration-plus-rapide))

---

## 2. Installation

Téléchargez le package SpaceBench (ZIP) et extrayez-le :

```bash
unzip spacebench.zip -d ~/workspace/spacebench
cd ~/workspace/spacebench
```

---

## 3. Lancer l'application

Choisissez l'une des deux méthodes ci-dessous selon votre flux de travail.

### 3a. Sans Docker (Windows uniquement — itération rapide)

Lancez le script fourni pour démarrer le frontend, le backend, le serveur de documentation et le moteur POD directement sur votre machine :

```powershell
.\run_the_app_dev.bat
```

| Service  | URL                                        |
|----------|--------------------------------------------|
| Frontend | [http://localhost:4200](http://localhost:4200) |
| Backend  | [http://localhost:8000](http://localhost:8000) |
| Documentation | [http://localhost:8001](http://localhost:8001) |
| Moteur POD | [http://localhost:8005](http://localhost:8005) |

!!! warning "Prérequis"
    Cette méthode nécessite **Node.js**, **Python 3.10+** et **PostgreSQL 16** installés localement. Les paramètres de base de données peuvent être fournis via les variables d'environnement ou le fichier de configuration backend. Docker n'est pas requis mais est recommandé en production.

---

### 3b. Avec Docker (multiplateforme — recommandé)

Sur Windows, ouvrez d'abord **Docker Desktop**, ensuite :

Si vous souhaitez démarrer le programme en local 

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Si vous souhaitez démarrer le programme de manière publique sur Internet

```bash
docker compose -f docker-compose.yml -f docker-compose.public.yml up -d
```

Une fois les conteneurs démarrés, tous les services sont disponibles localement :

| Service                   | URL                                                        |
|---------------------------|------------------------------------------------------------|
| Frontend (Angular)        | [http://localhost:8080](http://localhost:8080)             |
| Documentation (MkDocs)    | [http://localhost:8080/docs](http://localhost:8080/docs)   |
| Backend API (Swagger)     | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) |
| Moteur POD                | [http://localhost:8002](http://localhost:8002)             |
| pgAdmin                   | [http://localhost:5050](http://localhost:5050)             |

!!! note
    L'API backend fonctionne en interne sur le port `8000` et est proxifiée via le conteneur frontend.

--- 

## 4. Utiles

Que ce soit dans le Backend ou dans le moteur POD, vous pouvez effectuer certaines configurations particulières dans **app/core/settings.py**


```bash
# Show all prints in the terminal
DEBUG_MODE: bool = False

# Use to reset DB model (/!\ THIS DROPS EVERYTHING /!\)
RESET_DB: bool = True
```


---

## 5. Connexion

Utilisez les identifiants par défaut pour vous connecter :

| Champ          | Valeur      |
|----------------|-------------|
| Utilisateur    | `usertest`  |
| Mot de passe   | `CHANGE_ME___kKbvtu3LbI6yYQltgWdz` |
