from __future__ import annotations

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Session(Base):
    """Screening session lifecycle: created → uploaded → analyzed."""
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="created")
    video_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    result: Mapped[Optional["AnalysisResult"]] = relationship(
        "AnalysisResult", back_populates="session", uselist=False
    )


class AnalysisResult(Base):
    """
    Stores ML analysis output as CODES — no human-readable text.
    The frontend translates all codes into the user's chosen language.

    NOTE: screening data only — NOT a diagnosis.
    """
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("sessions.id"))

    # Numeric scores (nullable when quality_failed=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_score: Mapped[float] = mapped_column(Float)

    # Enum codes — frontend maps to translated text
    risk_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # low|moderate|elevated|None
    summary_code: Mapped[str] = mapped_column(String)                         # e.g. "low_risk_summary"
    recommendation_codes: Mapped[str] = mapped_column(Text)                   # JSON list of codes
    quality_failed: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_issues: Mapped[str] = mapped_column(Text, default="[]")           # JSON list of codes
    quality_metrics: Mapped[str] = mapped_column(Text, default="{}")          # JSON debug metrics

    # Feature-extraction output. These are research/debug artifacts, not user-facing diagnosis.
    feature_paths: Mapped[str] = mapped_column(Text, default="{}")              # JSON paths to CSV/JSON feature tables
    session_features_json: Mapped[str] = mapped_column(Text, default="{}")      # JSON session-level features
    model_version: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    model_explanation: Mapped[str] = mapped_column(Text, default="{}")          # JSON explainability/debug info

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["Session"] = relationship("Session", back_populates="result")
