from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
from fastapi import UploadFile

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "data" / "raw" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# Maximum upload size: 10 MB
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024

# Only CSV files are accepted
ALLOWED_EXTENSIONS = {".csv"}

COLUMN_ALIASES = {
    "State Name": "state",
    "City Name": "city",
    "Year": "year",
    "Month": "month",
    "Day of Week": "day_of_week",
    "Time of Day": "time",
    "Accident Severity": "severity",
    "Number of Vehicles Involved": "num_vehicles",
    "Vehicle Type Involved": "vehicle_type",
    "Weather Conditions": "weather",
    "Road Type": "road_type",
    "Road Condition": "road_condition",
    "Lighting Conditions": "lighting_conditions",
    "Traffic Control Presence": "traffic_control_presence",
    "Speed Limit (km/h)": "speed_limit_kmh",
    "Driver Age": "driver_age",
    "Driver Gender": "driver_gender",
    "Driver License Status": "driver_license_status",
    "Alcohol Involvement": "alcohol_involved",
    "Accident Location Details": "accident_location_details",
}

REQUIRED_COLUMNS = {
    "state",
    "city",
    "year",
    "month",
    "day_of_week",
    "time",
    "num_vehicles",
    "vehicle_type",
    "weather",
    "road_type",
    "road_condition",
    "lighting_conditions",
    "traffic_control_presence",
    "speed_limit_kmh",
    "driver_age",
    "driver_gender",
    "driver_license_status",
    "alcohol_involved",
    "accident_location_details",
}


def _sanitize_filename(raw_name: str) -> str:
    """Sanitize a user-provided filename to prevent path traversal attacks.

    Strips directory components and replaces unsafe characters.
    """
    # Extract only the basename — removes any directory traversal components
    basename = Path(raw_name).name

    # Replace any remaining dangerous characters
    safe_name = re.sub(r"[^\w.\-]", "_", basename)

    # Ensure it's not empty after sanitization
    if not safe_name or safe_name.startswith("."):
        safe_name = "uploaded_dataset.csv"

    return safe_name


def save_uploaded_dataset(file: UploadFile) -> dict:
    if not file.filename:
        raise ValueError("Uploaded file must have a filename.")

    # ── Validate file extension ─────────────────────────────────────
    raw_ext = Path(file.filename).suffix.lower()
    if raw_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Only CSV files are accepted. Received file with extension '{raw_ext}'."
        )

    # ── Sanitize filename ───────────────────────────────────────────
    safe_name = _sanitize_filename(file.filename)

    # ── Read contents with size limit ───────────────────────────────
    contents = file.file.read(MAX_UPLOAD_SIZE_BYTES + 1)
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise ValueError(
            f"Uploaded file is too large. Maximum allowed size is "
            f"{MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
        )

    saved_path = UPLOAD_DIR / safe_name
    saved_path.write_bytes(contents)

    # ── Parse CSV with error handling ───────────────────────────────
    try:
        dataset = pd.read_csv(saved_path)
    except Exception as exc:
        # Remove the corrupted file
        saved_path.unlink(missing_ok=True)
        raise ValueError(
            f"Could not parse the uploaded CSV file: {exc}"
        ) from exc

    dataset = dataset.rename(columns=COLUMN_ALIASES)

    missing_columns = sorted(REQUIRED_COLUMNS - set(dataset.columns))
    if missing_columns:
        return {
            "status": "uploaded-with-missing-columns",
            "file_path": str(saved_path.relative_to(ROOT)),
            "rows": int(len(dataset)),
            "columns": list(dataset.columns),
            "missing_columns": missing_columns,
        }

    return {
        "status": "uploaded-successfully",
        "file_path": str(saved_path.relative_to(ROOT)),
        "rows": int(len(dataset)),
        "columns": list(dataset.columns),
    }
