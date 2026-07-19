from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    status: str
    video_path: Optional[str] = None
    model_config = {"from_attributes": True}


class AnalysisResultResponse(BaseModel):
    """
    All text fields are CODES — the frontend translates them.
    No human-readable strings are returned by the backend.
    """
    session_id: str
    risk_score: Optional[float]          # None when quality_failed
    risk_level: Optional[str]            # "low" | "moderate" | "elevated" | None
    quality_score: float
    quality_failed: bool
    quality_issues: List[str]            # codes: ["lighting_low", ...]
    quality_metrics: Dict[str, Any] = {} # local/dev debugging metrics
    feature_summary: Dict[str, Any] = {} # key session-level features for dev/demo
    attention_score: Optional[float] = None
    attention_level: Optional[str] = None
    score_breakdown: Dict[str, float] = {}
    score_explanation: Optional[str] = None
    risk_confidence: Optional[float] = None
    risk_confidence_type: Optional[str] = None
    top_contributing_factors: List[Dict[str, Any]] = []
    model_version: Optional[str] = None
    summary_code: str                    # e.g. "low_risk_summary"
    recommendation_codes: List[str]      # e.g. ["not_diagnosis", "consult_specialist"]
    created_at: datetime
    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str


class FeatureBundleResponse(BaseModel):
    session_id: str
    quality_metrics: Dict[str, Any]
    frame_preview: List[Dict[str, Any]]
    frame_features: List[Dict[str, Any]]
    phase_features: List[Dict[str, Any]]
    session_features: Dict[str, Any]
    attention_score: Optional[float] = None
    attention_level: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    risk_details: Dict[str, Any]
    visualizations: Dict[str, Any] = {}
    downloads: Dict[str, str]
    medical_disclaimer: str
