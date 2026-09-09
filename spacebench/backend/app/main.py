from contextlib import asynccontextmanager
from starlette.staticfiles import StaticFiles

from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
from fastapi.openapi.docs import get_redoc_html

from app.core.database import ensure_database_exists, init_models
from app.migrations.seed import seed_default_runs
import app.models.pod


# ══════════════════ LIFESPAN ══════════════════ #

@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_database_exists()
    await init_models()          # drops + recreates all tables
    await seed_default_runs()   # fill with seed data
    yield


# ══════════════════ APP ══════════════════ #

app = FastAPI(
    lifespan=lifespan,
    title="SpaceBench API",
    description="""
    Open Source Framework for Precise Orbit Determination

    Author: Raphaël Louys  
    Institution: Université de Namur  
    Degree: Master en Informatique (Horaire Décalé)  
    Year: 2025  
    """,
    version="1.0.0",
    contact={
        "name": "Raphaël Louys",
        "email": "contact@harutech.be",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

# ══════════════════ LOGGING ══════════════════ #

logging.basicConfig(
    level=logging.INFO,
    filename='app.log',
    filemode='a',
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ══════════════════ CORS Middleware ══════════════════ #

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://localhost:8080",
        "http://127.0.0.1:4200",
        "http://127.0.0.1:8080",
        "http://spacebench.harutech.be:4200"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# ══════════════════ ROUTING ══════════════════ #

from app.routers.files import router as files_router
from app.routers.runs import router as runs_router
from app.routers.tests import router as test_router

app.include_router(files_router)
app.include_router(runs_router)
app.include_router(test_router)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ══════════════════ TEST ROUTE

@app.get("/health")
def health():
   return {"status": "ok"}

''' ReDoc '''


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
    )
