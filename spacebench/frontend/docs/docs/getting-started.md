# Getting Started

## 1. Prerequisites

Make sure you have the following installed:

- **Docker** (version 24 or later) and **Docker Compose** — required for the recommended path
- **Node.js**, **Python 3.10+**, and **PostgreSQL 16** — only required if running without Docker (see [§ 3a](#3a-without-docker-windows-only-faster-dev-iteration))

---

## 2. Installation

Download the SpaceBench package (ZIP) and extract it:

```bash
unzip spacebench.zip -d ~/workspace/spacebench
cd ~/workspace/spacebench
```

---

## 3. Running the Application

Choose one of the two methods below depending on your workflow.

### 3a. Without Docker (Windows only — faster dev iteration)

Run the provided script to start the frontend, backend, documentation server, and POD engine directly on your machine:

```powershell
.\run_the_app_dev.bat
```

| Service  | URL                                        |
|----------|--------------------------------------------|
| Frontend | [http://localhost:4200](http://localhost:4200) |
| Backend  | [http://localhost:8000](http://localhost:8000) |
| Documentation | [http://localhost:8001](http://localhost:8001) |
| POD Engine | [http://localhost:8005](http://localhost:8005) |

!!! warning "Requirements"
    This method requires **Node.js**, **Python 3.10+**, and **PostgreSQL 16** installed locally. Database settings can be provided through environment variables or the backend settings file. Docker is not required but is recommended for production.

---

### 3b. With Docker (Windows, Linux — recommended)

On Windows, open **Docker Desktop** first, then:

If you want to run it locally :
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```
If you it to run it public : 
```bash
docker compose -f docker-compose.yml -f docker-compose.public.yml up -d
```

Once containers are up, all services are available locally:

| Service                   | URL                                                        |
|---------------------------|------------------------------------------------------------|
| Frontend (Angular)        | [http://localhost:8080](http://localhost:8080)             |
| Documentation (MkDocs)    | [http://localhost:8080/docs](http://localhost:8080/docs)   |
| Backend API (Swagger)     | [http://localhost:8000/api/docs](http://localhost:8000/api/docs) |
| POD Engine                | [http://localhost:8002](http://localhost:8002)             |
| pgAdmin                   | [http://localhost:5050](http://localhost:5050)             |

!!! note
    The backend API runs internally on port `8000` and is proxied through the frontend container.

--- 

## 4. Utils

Whether in the Backend or the POD engine, you can configure specific settings in **app/core/settings.py**

```bash
# Show all prints in the terminal
DEBUG_MODE: bool = False

# Use to reset DB model (/!\ THIS DROPS EVERYTHING /!\)
RESET_DB: bool = True
```

---

## 5. Login

Use the default credentials to sign in:

| Field    | Value       |
|----------|-------------|
| Username | `usertest`  |
| Password | `CHANGE_ME___kKbvtu3LbI6yYQltgWdz` |
