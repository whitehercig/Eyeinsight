"""
EyeInsight Backend — FastAPI application entry point.

IMPORTANT MEDICAL DISCLAIMER:
EyeInsight is a SCREENING SUPPORT TOOL only.
It does NOT diagnose any medical condition.
All results are preliminary behavioral indicators.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routes import sessions, analysis

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EyeInsight API",
    description=(
        "Backend for EyeInsight — an AI-powered developmental screening support tool. "
        "NOT a diagnostic system. Results are preliminary only."
    ),
    version="0.5.0",
)

# Allow the frontend (Vite dev server) to call the backend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite default
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sessions.router)
app.include_router(analysis.router)


@app.get("/api/health")
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}
