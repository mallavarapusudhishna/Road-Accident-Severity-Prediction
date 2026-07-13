from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import PredictionRequest, PredictionResponse
from backend.services.database_service import save_prediction_records
from backend.services.model_service import load_model_metadata
from backend.services.prediction_service import predict_from_request
from backend.services.statistics_service import build_statistics_payload
from backend.services.upload_service import save_uploaded_dataset

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    prediction = predict_from_request(payload)
    save_prediction_records(payload, prediction.predicted_severity, prediction.confidence)
    return prediction


@router.post("/upload")
def upload_dataset(file: UploadFile = File(...)) -> dict:
    return save_uploaded_dataset(file)


@router.get("/statistics")
def statistics() -> dict:
    return build_statistics_payload()


@router.get("/model-info")
def model_info() -> dict:
    metadata = load_model_metadata()
    return metadata
