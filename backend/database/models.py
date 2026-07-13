from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AccidentRecord(Base):
    __tablename__ = "accidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(255), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[str] = mapped_column(String(50), nullable=False)
    day_of_week: Mapped[str] = mapped_column(String(50), nullable=False)
    time: Mapped[str] = mapped_column(String(20), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    num_vehicles: Mapped[int] = mapped_column(Integer, nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(255), nullable=False)
    driver_age: Mapped[int] = mapped_column(Integer, nullable=False)
    driver_gender: Mapped[str] = mapped_column(String(50), nullable=False)
    license_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weather: Mapped[str] = mapped_column(String(255), nullable=False)
    lighting: Mapped[str] = mapped_column(String(255), nullable=False)
    road_type: Mapped[str] = mapped_column(String(255), nullable=False)
    road_condition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    traffic_control_presence: Mapped[str | None] = mapped_column(String(255), nullable=True)
    accident_location_details: Mapped[str | None] = mapped_column(String(255), nullable=True)
    speed_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    alcohol_involved: Mapped[str] = mapped_column(String(20), nullable=False)
    accident_hour: Mapped[int | None] = mapped_column(Integer, nullable=True)
    time_of_day: Mapped[str | None] = mapped_column(String(50), nullable=True)
    driver_age_group: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_multi_vehicle: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_weekend: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_night: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_peak_hour: Mapped[str | None] = mapped_column(String(10), nullable=True)
    confidence: Mapped[float | None] = mapped_column(nullable=True)


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state: Mapped[str] = mapped_column(String(255), nullable=False)
    prediction: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(nullable=True)
    input_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )
