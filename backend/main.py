"""
EyeInsight Backend — FastAPI application entry point.

IMPORTANT MEDICAL DISCLAIMER:
EyeInsight is an unvalidated research prototype.
It does NOT diagnose any medical condition or estimate clinical risk.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from database import engine, Base
from routes import analysis, camera, sessions

# Create all DB tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="EyeInsight API",
    description=(
        "Backend for EyeInsight — a camera-based visual-attention research prototype. "
        "It provides descriptive technical metrics, not diagnoses or clinical risk estimates."
    ),
    version="0.6.0",
)

# Allow the frontend (Vite dev server) to call the backend during development
cors_origins = [origin.strip() for origin in os.getenv("EYEINSIGHT_CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(sessions.router)
app.include_router(analysis.router)
app.include_router(camera.router)


@app.get("/api/health")
def health_check():
    """Simple liveness probe."""
    return {"status": "ok"}


static_dir = Path(os.getenv("EYEINSIGHT_STATIC_DIR", ""))
index_file = static_dir / "index.html"


if index_file.is_file():
    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def serve_frontend(path: str) -> FileResponse:
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        requested_file = static_dir / path
        if path and requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(index_file)
