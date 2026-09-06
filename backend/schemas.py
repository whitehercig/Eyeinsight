from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: str
    created_at: datetime
    status: str
    model_config = {"from_attributes": True}


class CameraReadinessResponse(BaseModel):
    ready: bool
    checks: Dict[str, bool]
    issues: List[str]
    metrics: Dict[str, float]


class AnalysisResultResponse(BaseModel):
    """
    All text fields are CODES — the frontend translates them.
    Legacy risk fields remain nullable for API compatibility. The current
    research-prototype pipeline does not generate a clinical risk estimate.
    """
    session_id: str
    risk_score: Optional[float]          # always None in the current prototype
    risk_level: Optional[str]            # always None in the current prototype
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
    summary_code: str                    # e.g. "technical_session_complete"
    recommendation_codes: List[str]      # e.g. ["not_diagnosis"]
    source_video_deleted: bool = False
    is_demo: bool = False
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
