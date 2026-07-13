from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router as api_router
from backend.database.session import init_db

app = FastAPI(
    title="Road Accident Severity Prediction API",
    version="1.0.0",
    description="FastAPI backend that serves predictions from the notebook-trained accident severity model.",
)


@app.on_event("startup")
def startup_event() -> None:
    init_db()

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
