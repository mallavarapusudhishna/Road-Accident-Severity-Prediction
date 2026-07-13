from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import UploadFile

ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = ROOT / "data" / "raw" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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
    "Speed Limit (km/h)": "speed_limit_(km/h)",
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
    "speed_limit_(km/h)",
    "driver_age",
    "driver_gender",
    "driver_license_status",
    "alcohol_involved",
    "accident_location_details",
}


def save_uploaded_dataset(file: UploadFile) -> dict:
    if not file.filename:
        raise ValueError("Uploaded file must have a filename.")

    saved_path = UPLOAD_DIR / file.filename
    contents = file.file.read()
    saved_path.write_bytes(contents)

    dataset = pd.read_csv(saved_path)
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
