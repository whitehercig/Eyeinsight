# EyeInsight MVP

EyeInsight is a camera-based visual-attention **research MVP** for structured sessions in pediatric-clinic workflows. It is not a medical device, has not been clinically validated, and does not diagnose autism or any other condition.

The public build includes two separate flows:

- **Camera session:** a short pre-recording readiness check validates lighting, face position, distance, and stability before recording is unlocked.
- **Safe report demo:** a synthetic, clearly labelled session demonstrates the report without opening the camera or using personal data.

## Pipeline

`guided stimulus → temporary video upload → quality gate + MediaPipe Face Mesh → frame features → phase features → session features → technical dashboard/PDF → raw-video deletion`

The feature extractor runs once per analysis. It uses MediaPipe Face Mesh with refined iris landmarks, OpenCV quality measures, `solvePnP` head-pose estimates, gaze smoothing, blink events, and phase-aware aggregation. The current product displays descriptive engineering metrics only; it does not generate a clinical risk score.

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

Uploaded sessions persist their lifecycle (`uploaded`, `processing`, `analyzed`, `quality_failed`, or `analysis_failed`). The browser stores only the pending session identifier so an interrupted analysis can resume through status polling; it does not store the recorded video in local storage.

## Deploy free on Render

The repository includes a single-service `render.yaml`: it builds the React frontend and serves it from FastAPI on the same public URL. In Render, select **New → Blueprint**, connect `whitehercig/Eyeinsight`, and choose the `main` branch. The health check is `/api/health`.

This configuration is suitable for a public MVP demo only. Render free services can take about a minute to wake after inactivity and their local SQLite database and generated files are erased on restart or sleep. The Docker deployment samples video at up to 4 FPS and resizes frames to 320 px before Face Mesh inference to fit the free CPU tier; local runs retain full-frame processing by default. The raw source video is deleted automatically after successful feature extraction, and derived session data is purged after 24 hours when a new session starts. Do not use this deployment for clinical decisions or real patient workflows.

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
- `session_report_{language}.pdf` — one-page technical summary generated on request. It includes data quality, descriptive attention proxies, and phase-level screen-gaze proxy values.

The result page lets a user download each required CSV/JSON file. The data endpoint is `GET /api/sessions/{session_id}/features`; artifact downloads are `GET /api/sessions/{session_id}/downloads/{filename}`.

## API

- `POST /api/sessions`
- `POST /api/sessions/demo` creates a synthetic report without camera or personal data.
- `GET /api/sessions/{session_id}` returns the durable processing status.
- `POST /api/camera-check` validates a short burst of camera stills before recording.
- `POST /api/sessions/{session_id}/upload-video`
- `POST /api/analyze-session/{session_id}` (`?retry=true` explicitly restarts a stuck processing job.)
- `GET /api/sessions/{session_id}/result`
- `GET /api/sessions/{session_id}/features`
- `GET /api/sessions/{session_id}/downloads/{filename}`
- `GET /api/sessions/{session_id}/clinical-report?lang=ru` (`ru`, `kz`, or `en`)
- `DELETE /api/sessions/{session_id}` permanently removes the session video, generated artifacts, and database records.

## Metrics and safety

The technical attention proxy is a deterministic weighted combination of tracking quality, face visibility, head/gaze stability, center fixation, looking-away ratio, phase consistency, and usable frames. It is an engineering summary for pipeline development, not a validated clinical scale.

A low-quality recording receives no result beyond the quality findings. The heatmap, gaze path, target alignment, and response latency are **uncalibrated technical proxies**, not clinical eye-tracking measurements and not diagnostic evidence. Clinical use requires a locked protocol, ethics/privacy review, prospective data collection, and validation against an accepted reference standard.

Set `EYEINSIGHT_DELETE_SOURCE_VIDEO=false` only in a controlled research environment with an approved retention policy when raw videos must be retained for validation.

Set `EYEINSIGHT_SESSION_TTL_HOURS` to change the derived-data retention window. A non-positive value disables automatic expiry and should be used only in a controlled environment.
