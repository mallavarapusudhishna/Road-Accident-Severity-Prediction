# WORKAROUND: NumPy 2.x throws TypeError when checking np.isnan() on 
# object arrays containing strings. Patch it before any other imports!
import numpy as np
_orig_isnan = np.isnan
def _safe_isnan(x, *args, **kwargs):
    try:
        return _orig_isnan(x, *args, **kwargs)
    except TypeError:
        x_obj = np.asarray(x, dtype=object)
        res = np.zeros(x_obj.shape, dtype=bool)
        for idx, val in np.ndenumerate(x_obj):
            if isinstance(val, float) and val != val:
                res[idx] = True
        return res
np.isnan = _safe_isnan

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.database.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook (replaces deprecated @app.on_event)."""
    # ── Startup ──────────────────────────────────────────────────────
    import time
    t_start = time.perf_counter()
    
    init_db()
    from backend.services.prediction_service import init_prediction_service
    
    try:
        init_prediction_service()
    except Exception as exc:
        logging.getLogger(__name__).error("Prediction service failed to load: %s", exc)
        
    t_elapsed = (time.perf_counter() - t_start) * 1000.0
    logging.getLogger(__name__).info("FastAPI startup completed in %.0f ms", t_elapsed)
    
    yield
    # ── Shutdown (nothing needed currently) ──────────────────────────


app = FastAPI(
    title="Road Accident Severity Prediction API",
    version="1.0.0",
    description="FastAPI backend that serves predictions from the notebook-trained accident severity model.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/")
def root() -> dict:
    return {
        "message": "Road Accident Severity Prediction API is running.",
        "docs": "/docs",
    }
