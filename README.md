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

## Deploy free on Render

The repository includes a single-service `render.yaml`: it builds the React frontend and serves it from FastAPI on the same public URL. In Render, select **New → Blueprint**, connect `whitehercig/Eyeinsight`, and choose the `main` branch. The health check is `/api/health`.

This configuration is suitable for a public MVP demo only. Render free services can take about a minute to wake after inactivity and their local SQLite database, uploaded videos, and generated files are erased on restart or sleep. Do not use this deployment to store clinical or personal data.

### Run with Docker

```bash
docker compose up --build
```

Open `http://localhost:8080`. Docker keeps the SQLite database, uploaded videos, and generated features in the `eyeinsight-data` volume.

## Generated artifacts

Each analysis writes to `backend/features/{session_id}/`:

- `frame_features.csv` — raw technical/behavioral proxy features per decoded frame.
- `phase_features.csv` — descriptive, fixation, motion, blink, gaze, and reaction aggregates per stimulus phase.
- `session_features.csv` and `session_features.json` — session-level inputs for inference.
- `analysis_result.json` — persisted API result suitable for export.
- `clinical_report_{language}.pdf` — one-page clinician-oriented summary generated on request. It includes technical data quality, descriptive attention indicators, and phase-level screen-gaze proxy values.

The result page lets a user download each required CSV/JSON file. The data endpoint is `GET /api/sessions/{session_id}/features`; artifact downloads are `GET /api/sessions/{session_id}/downloads/{filename}`.

## API

- `POST /api/sessions`
- `POST /api/sessions/{session_id}/upload-video`
- `POST /api/analyze-session/{session_id}`
- `GET /api/sessions/{session_id}/result`
- `GET /api/sessions/{session_id}/features`
- `GET /api/sessions/{session_id}/downloads/{filename}`
- `GET /api/sessions/{session_id}/clinical-report?lang=ru` (`ru`, `kz`, or `en`)
- `DELETE /api/sessions/{session_id}` permanently removes the session video, generated artifacts, and database records.

## Scoring and safety

The attention score is a deterministic weighted combination of tracking quality, face visibility, head/gaze stability, center fixation, looking-away ratio, phase consistency, and usable frames. The risk-like screening indicator is a deterministic, transparent rule set over these aggregates. Its displayed confidence is only **technical input reliability**, never diagnostic or clinical confidence.

A low-quality recording receives no risk score. Any output remains a preliminary screening indicator and must be interpreted with a qualified professional when concerns exist. The heatmap, gaze path, target alignment, and response latency are **uncalibrated technical proxies**, not clinical eye-tracking measurements and not diagnostic evidence.
