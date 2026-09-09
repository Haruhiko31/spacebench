@echo off
REM ============================================
REM  Dev Launcher - Angular + FastAPI
REM  Starts backend and frontend in separate terminals
REM ============================================

SET ROOT_DIR=%~dp0

REM --- Launch Backend in a new terminal ---
start "Backend - FastAPI" cmd /k "cd /d %ROOT_DIR%backend && (if not exist venv python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt && pip install -r requirements-dev.txt && uvicorn app.main:app --reload"

REM --- Launch MkDocs docs in a new terminal, using backend venv ---
start "Docs - MkDocs" cmd /k "cd /d %ROOT_DIR%backend && timeout /t 15 /nobreak >nul && call venv\Scripts\activate && cd /d %ROOT_DIR%frontend\docs && mkdocs serve --dev-addr=0.0.0.0:8080"

REM --- Small delay to let backend start first ---
timeout /t 3 /nobreak >nul

REM --- Launch Frontend in a new terminal ---
start "Frontend - Angular" cmd /k "cd /d %ROOT_DIR%frontend && (if not exist node_modules npm install --legacy-peer-deps) && npm start"

REM --- Launch POD Engine in a new terminal ---
start "POD Engine - FastAPI" cmd /k "cd /d %ROOT_DIR%pod-engine && (if not exist venv python -m venv venv) && call venv\Scripts\activate && pip install -r requirements.txt && pip install -r requirements-dev.txt && uvicorn app.main:app --reload --port 8002"

echo.
echo All terminals launched. Close this window anytime.
echo   Backend:  http://localhost:8000
echo   POD Engine:  http://localhost:8002
echo   Frontend: http://localhost:4200
echo   Docs:     http://localhost:8080
