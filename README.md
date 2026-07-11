# EyeInsight MVP

EyeInsight is an AI-assisted visual-attention **screening support** prototype. It is not a medical device and does not diagnose autism or any other condition.

## Pipeline

`video upload → every-frame quality + MediaPipe Face Mesh → frame_features.csv → phase_features.csv → session_features.csv/json → explainable attention score → deterministic screening indicator → dashboard and downloads`

The feature extractor runs once per analysis. It uses MediaPipe Face Mesh with refined iris landmarks, OpenCV quality measures, `solvePnP` head-pose estimates, gaze smoothing, blink events, and phase-aware aggregation.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite development proxy forwards `/api` to FastAPI.

## Generated artifacts

Each analysis writes to `backend/features/{session_id}/`:

- `frame_features.csv` — raw technical/behavioral proxy features per decoded frame.
- `phase_features.csv` — descriptive, fixation, motion, blink, gaze, and reaction aggregates per stimulus phase.
- `session_features.csv` and `session_features.json` — session-level inputs for inference.
- `analysis_result.json` — persisted API result suitable for export.

The result page lets a user download each required CSV/JSON file. The data endpoint is `GET /api/sessions/{session_id}/features`; artifact downloads are `GET /api/sessions/{session_id}/downloads/{filename}`.

## API

- `POST /api/sessions`
- `POST /api/sessions/{session_id}/upload-video`
- `POST /api/analyze-session/{session_id}`
- `GET /api/sessions/{session_id}/result`
- `GET /api/sessions/{session_id}/features`
- `GET /api/sessions/{session_id}/downloads/{filename}`

## Scoring and safety

The attention score is a deterministic weighted combination of tracking quality, face visibility, head/gaze stability, center fixation, looking-away ratio, phase consistency, and usable frames. The risk-like screening indicator is a deterministic, transparent rule set over these aggregates. Its displayed confidence is only **technical input reliability**, never diagnostic or clinical confidence.

A low-quality recording receives no risk score. Any output remains a preliminary screening indicator and must be interpreted with a qualified professional when concerns exist.
