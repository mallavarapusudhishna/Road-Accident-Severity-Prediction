import logging
import time

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.models.schemas import PredictionRequest, PredictionResponse, ValidationErrorResponse
from backend.services.database_service import save_prediction_records
from backend.services.model_service import load_model_metadata
from backend.services.prediction_service import predict_from_request
from backend.services.statistics_service import build_statistics_payload
from backend.services.upload_service import save_uploaded_dataset
from backend.services.validation_service import validate_prediction_request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.post(
    "/predict",
    response_model=PredictionResponse,
    responses={422: {"model": ValidationErrorResponse}},
)
def predict(payload: PredictionRequest) -> PredictionResponse:
    start_total = time.perf_counter()
    logger.info("predict_request state=%s city=%s year=%s", payload.state, payload.city, payload.year)

    # ── Real-world validation (before model prediction) ─────────────
    validation_errors = validate_prediction_request(payload)
    if validation_errors:
        logger.warning("predict_rejected reasons=%s", validation_errors)
        raise HTTPException(
            status_code=422,
            detail={
                "detail": "The submitted inputs are not logically possible.",
                "validation_errors": validation_errors,
            },
        )

    # predict_from_request now returns (response, timings, derived_fields).
    try:
        prediction, timings, derived_fields = predict_from_request(payload)
    except RuntimeError as exc:
        logger.error("predict_model_error: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Prediction service is currently unavailable. Please try again later.",
        )

    # Persist only what DB schema supports right now (best-effort).
    start_db = time.perf_counter()
    try:
        save_prediction_records(payload, prediction.predicted_severity, prediction.confidence, derived_fields)
    except Exception:
        logger.exception("Database write failed — prediction result is still returned")
    timings["database"] = (time.perf_counter() - start_db) * 1000.0

    total_ms = (time.perf_counter() - start_total) * 1000.0
    timings["total"] = total_ms

    logger.info(
        "predict_success severity=%s confidence=%.4f",
        prediction.predicted_severity,
        prediction.confidence,
    )

    timing_log = (
        f"Frame build:      {timings.get('frame_build', 0):.2f} ms\n"
        f"Preprocessing:    {timings['preprocessing']:.2f} ms\n"
        f"Prediction:       {timings['prediction']:.2f} ms\n"
        f"SHAP (compute):   {timings.get('shap_values', 0):.2f} ms\n"
        f"SHAP (postproc):  {timings.get('shap_postprocess', 0):.2f} ms\n"
        f"Database:         {timings['database']:.2f} ms\n"
        f"Total:            {timings['total']:.2f} ms"
    )
    logger.info("Timing breakdown:\n%s", timing_log)

    return prediction


@router.post("/upload")
def upload_dataset(file: UploadFile = File(...)) -> dict:
    try:
        result = save_uploaded_dataset(file)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        logger.exception("upload_failed")
        raise HTTPException(status_code=500, detail="Failed to process uploaded file.")

    # Return 422 when the dataset is missing required columns
    if result.get("status") == "uploaded-with-missing-columns":
        raise HTTPException(status_code=422, detail=result)

    return result


@router.get("/statistics")
def statistics() -> dict:
    try:
        return build_statistics_payload()
    except Exception:
        logger.exception("statistics_failed")
        raise HTTPException(
            status_code=503,
            detail="Statistics are currently unavailable. The processed dataset may be missing.",
        )


@router.get("/model-info")
def model_info() -> dict:
    try:
        metadata = load_model_metadata()
        return metadata
    except Exception:
        logger.exception("model_info_failed")
        raise HTTPException(
            status_code=503,
            detail="Model information is currently unavailable.",
        )
