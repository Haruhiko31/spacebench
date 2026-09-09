from fastapi import FastAPI, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging


# ══════════════════ APP ══════════════════ #

app = FastAPI()

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
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8005",
        "http://127.0.0.1:8005",
        "http://localhost:4200",
        "http://127.0.0.1:4200",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "http://spacebench.harutech.be:8000",
        "http://spacebench.harutech.be:8005"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from .routers.analysis import router as runs_router
from .routers.tests.test import router as test_router
app.include_router(runs_router)
app.include_router(test_router)

# ══════════════════ TEST ROUTE

@app.get("/health")
def health():
   return {"status": "ok"}
