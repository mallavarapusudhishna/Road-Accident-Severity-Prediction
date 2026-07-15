from __future__ import annotations

import json
import logging

from backend.database import session as db_session
from backend.database.models import AccidentRecord, PredictionRecord
from backend.models.schemas import PredictionRequest

logger = logging.getLogger(__name__)


def save_prediction_records(
    payload: PredictionRequest,
    predicted_severity: str,
    confidence: float,
    derived_fields: dict,
) -> None:
    """Persist accident and prediction records.

    This is a **best-effort** operation.  If the database is unavailable the
    prediction response is still returned to the caller — the error is logged
    but not re-raised.

    Parameters
    ----------
    derived_fields
        Pre-computed derived fields from predict_from_request().
        Passed in to avoid a redundant build_derived_fields() call.
    """
    db = None
    try:
        db = db_session.SessionLocal()

        accident_record = AccidentRecord(
            state=payload.state,
            city=payload.city,
            year=payload.year,
            month=payload.month,
            day_of_week=payload.day_of_week,
            time=payload.time,
            severity=predicted_severity,
            num_vehicles=payload.num_vehicles,
            vehicle_type=payload.vehicle_type,
            driver_age=payload.driver_age,
            driver_gender=payload.driver_gender,
            license_status=payload.driver_license_status,
            weather=payload.weather,
            lighting=payload.lighting_conditions,
            road_type=payload.road_type,
            road_condition=payload.road_condition,
            traffic_control_presence=payload.traffic_control_presence,
            accident_location_details=payload.accident_location_details,
            speed_limit=payload.speed_limit_kmh,
            alcohol_involved=payload.alcohol_involved,
            accident_hour=derived_fields["accident_hour"],
            time_of_day=derived_fields["time_of_day"],
            driver_age_group=derived_fields["driver_age_group"],
            is_multi_vehicle=derived_fields["is_multi_vehicle"],
            is_weekend=derived_fields["is_weekend"],
            is_night=derived_fields["is_night"],
            is_peak_hour=derived_fields["is_peak_hour"],
            confidence=float(confidence),
        )
        prediction_record = PredictionRecord(
            state=payload.state,
            prediction=predicted_severity,
            confidence=float(confidence),
            input_payload=json.dumps(payload.model_dump(), default=str),
        )

        db.add(accident_record)
        db.add(prediction_record)
        db.commit()
    except Exception:
        if db is not None:
            try:
                db.rollback()
            except Exception:
                pass
        logger.exception("Failed to persist prediction records to database")
        # Best-effort: do NOT re-raise — the prediction result is still valid.
    finally:
        if db is not None:
            try:
                db.close()
            except Exception:
                pass
