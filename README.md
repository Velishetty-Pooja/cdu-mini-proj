# Indian Traffic Intelligence (ITI)

A real-time, locally runnable computer vision and traffic intelligence system tailored for Indian roadway monitoring. Built from scratch with **FastAPI**, **Ultralytics YOLO**, **ByteTrack**, **SQLite**, **ReportLab**, and **React + TypeScript + Vite + Tailwind CSS**.

---

## Primary Objectives & Operational Philosophy

1. **Zero Fake Detections**: No hardcoded results, mock predictions, simulated success messages, or synthetic detections in production code. Real inference runs locally using `yolov8n.pt`.
2. **Defensible Vehicle Counting**: Clearly separates frame-level detections from unique tracked vehicles (via ByteTrack persistent IDs), counts by class, and optional virtual counting line gates.
3. **Evidence-Based Direction Analysis**: Trajectory evaluation computes 2D displacement vectors over consecutive frames. Flags potential wrong-side movements only when minimum displacement, observation duration, and cosine directional thresholds are met.
4. **Honest Scientific Reporting**: Does **not** fabricate physical speeds in km/h without camera calibration homography matrices. Documents indigenous vehicle class limitations (e.g. Indian auto-rickshaws under standard COCO weights).

---

## System Architecture & Technical Stack

```
indian-traffic-intelligence/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & REST endpoints
│   │   ├── config.py            # System configuration, paths, and thresholds
│   │   ├── schemas.py           # Pydantic data schemas
│   │   ├── detector.py          # Real YOLO object detection & bounding box clipping
│   │   ├── tracker.py           # ByteTrack trajectory management & track metrics
│   │   ├── traffic_rules.py     # Wrong-side analysis, lane rules & counting lines
│   │   ├── congestion.py        # Road area occupancy & pedestrian density
│   │   ├── reports.py           # ReportLab PDF & structured CSV report generation
│   │   └── database.py          # SQLite persistence for analysis runs & traffic events
│   ├── tests/
│   │   ├── test_health.py               # Health & model readiness endpoint
│   │   ├── test_detection_schema.py     # Schema validation & missing weights error
│   │   ├── test_vehicle_counting.py     # Unique counts & duplicate prevention
│   │   ├── test_tracking.py             # Trajectory histories & displacement vectors
│   │   ├── test_wrong_way.py            # Direction analysis (7 test scenarios)
│   │   ├── test_lane_rules.py           # Bus lane, restricted zones, congestion
│   │   ├── test_uploads.py              # Media decoder validation & path traversal
│   │   └── test_reports.py              # CSV & ReportLab PDF validation
│   ├── samples/                 # Sample traffic images & videos
│   ├── storage/                 # Uploads, processed videos, evidence crops, SQLite DB
│   ├── requirements.txt         # Pinned Python dependencies
│   ├── .env.example             # Backend configuration template
│   └── yolov8n.pt               # Pretrained YOLOv8 weights (COCO 80 classes)
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components (Navbar, StatsCard, Charts, Modal)
│   │   ├── pages/               # Dashboard, Upload, Details, Events, History, Settings
│   │   ├── services/            # Axios API service client
│   │   ├── hooks/               # useAnalysisJob background polling hook
│   │   ├── types/               # TypeScript interfaces matching backend schemas
│   │   ├── App.tsx              # Root router & tab navigation
│   │   └── main.tsx             # React entrypoint
│   ├── package.json             # Frontend dependencies (React, Vite, Recharts, Lucide)
│   ├── vite.config.ts           # Vite proxy configuration
│   └── tsconfig.json            # TypeScript configuration
├── start-backend.ps1            # Windows 11 PowerShell backend launch script
├── start-frontend.ps1           # Windows 11 PowerShell frontend launch script
├── README.md                    # System documentation
└── .gitignore                   # Version control exclusions
```

---

## Machine Learning Model & Licensing

- **Object Detection Architecture**: Ultralytics YOLOv8 Nano (`yolov8n.pt`).
- **Model License**: GNU Affero General Public License v3.0 (AGPL-3.0). Open-source, non-commercial, and research use.
- **Dataset License**: Microsoft COCO dataset is licensed under Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Supported Traffic Classes**:
  - `Car` (COCO class ID 2)
  - `Motorcycle` (COCO class ID 3)
  - `Bus` (COCO class ID 5)
  - `Truck` (COCO class ID 7)
  - `Bicycle` (COCO class ID 1)
  - `Pedestrian` (COCO class ID 0 - Person)
- **Indian Vehicle Domain Context**:
  Standard COCO weights do not include a native `Auto-rickshaw` or `Three-wheeler` class. In standard operation, three-wheelers are identified as the closest visual vehicle classes (Car, Motorcycle, or Bus). When custom-trained weights on the Indian Driving Dataset (IDD) are loaded, the backend dynamically recognizes the `Auto-rickshaw` category.

---

## Windows 11 Local Setup & Execution Guide

### Prerequisites
- **Windows 11** (64-bit)
- **Python 3.12** installed and added to `PATH`
- **Node.js v20+** and **npm** installed

### PowerShell Execution Policy (If Script Execution is Blocked)
If you encounter `Execution_Policies` restriction in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Option A: 1-Click Startup Scripts

#### Terminal 1 (Backend):
```powershell
.\start-backend.ps1
```

#### Terminal 2 (Frontend):
```powershell
.\start-frontend.ps1
```

---

### Option B: Step-by-Step Manual Commands

#### Terminal 1: Backend Setup
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend Health Check**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Terminal 2: Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
- **Frontend Dashboard URL**: [http://localhost:5173](http://localhost:5173)

---

## REST API Specification

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System readiness, device, model version, and supported classes |
| `POST` | `/api/analyze/image` | Analyzes uploaded traffic image with real YOLO inference |
| `POST` | `/api/analyze/video` | Queues asynchronous background video tracking job |
| `GET` | `/api/jobs/{job_id}` | Polls progress (0-100%) and retrieves results of video job |
| `GET` | `/api/results/{analysis_id}` | Retrieves full analysis dossier and flagged events |
| `GET` | `/api/history` | Fetches persistent analysis audit trail from SQLite |
| `DELETE` | `/api/history/{analysis_id}` | Deletes analysis record and associated events |
| `GET` | `/api/reports/{analysis_id}/pdf` | Downloads ReportLab generated PDF audit dossier |
| `GET` | `/api/reports/{analysis_id}/csv` | Downloads structured CSV metrics report |
| `GET` | `/api/samples` | Lists available local sample test images and videos |
| `POST` | `/api/analyze/sample` | Runs analysis directly on sample media without re-upload |

---

## Automated Verification & Test Suite

The test suite validates the detection pipeline, mathematical direction analysis, trajectory tracking, counting line crossing logic, report generation, and upload security.

### Running Tests:
```powershell
cd backend
$env:PYTHONPATH="."
.\venv\Scripts\pytest.exe -v tests
```

### Test Suite Summary (28/28 Passing):
- `tests/test_health.py`: Validates `/api/health` response schema, supported classes, and unverified auto-rickshaw documentation.
- `tests/test_detection_schema.py`: BoundingBox schema validation, coordinate clipping, and explicit error handling on missing weights.
- `tests/test_vehicle_counting.py`: Distinguishes vehicles from pedestrians, prevents counting two-wheeler riders as independent pedestrians, verifies persistent unique vehicle aggregation across video frames, and tests virtual counting line crossings.
- `tests/test_tracking.py`: Trajectory displacement, lifetime tracking, and majority class voting.
- `tests/test_wrong_way.py`: Unit tests for:
  1. Movement in expected direction
  2. Movement against configured direction
  3. Negligible movement (stationary/jitter rejection)
  4. Noisy trajectories with overall correct flow
  5. Insufficient observation duration
  6. Dual-carriageway with separate configured lanes
  7. Missing travel direction configuration
- `tests/test_lane_rules.py`: BRTS bus lane vehicle restriction, restricted zone intrusion, and congestion density thresholds.
- `tests/test_uploads.py`: Extension rejection, corrupted image byte rejection, path traversal protection, and end-to-end synthetic image analysis.
- `tests/test_reports.py`: Validates CSV formatting, ReportLab PDF document creation (`%PDF-` header), and regression test for `VehicleSummary` attribute access with raw Pydantic instances.

---

## Feature Verification Checklist

- [x] **Vehicle Detection & Classification**: Real YOLO inference detecting Car, Motorcycle, Bus, Truck, Bicycle.
- [x] **Separation of Vehicles & Pedestrians**: Pedestrians categorized separately from vehicular volumes.
- [x] **Persistent Multi-Object Tracking**: ByteTrack assigns persistent IDs, maintains trajectories, and prevents double-counting.
- [x] **Evidence-Based Wrong-Side Detection**: Evaluates 2D trajectory vectors, displacement thresholds, cosine similarity, and captures evidence crops.
- [x] **Configurable Lane Rules**: Dedicated lane vehicle restrictions and restricted zone entry alerts.
- [x] **Congestion & Density Estimation**: Interpretable road area occupancy percentage (Low < 20%, Moderate 20-45%, High > 45%).
- [x] **Virtual Counting Lines**: Intersects trajectory vectors with configured lines and counts crossings.
- [x] **Annotated Media**: Output images and videos with bounding boxes, trajectory trails, and status HUD.
- [x] **Local SQLite Database**: Persists history, metadata, and violation records across server restarts.
- [x] **Report Generation**: Generates auditable CSV and publication-ready ReportLab PDF reports.
- [x] **React + Vite Dashboard**: Responsive UI with StatsCards, Recharts visualizations, Evidence modal, and live polling.

---

## Known Scientific Limitations & Disclaimers

1. **Real-World Speed in km/h**: Omitted by design. Physical velocity requires metric camera calibration and ground-plane homography. Estimating speed from uncalibrated 2D pixels produces arbitrary and legally indefensible numbers.
2. **Auto-Rickshaws & E-Rickshaws**: Standard COCO weights group them into Cars or Motorcycles. A fine-tuned model trained on Indian traffic datasets (e.g. IDD) is required for standalone three-wheeler categorization.
3. **Legal Status of Flagged Events**: All flagged wrong-side and lane violations represent algorithmic trajectory deviations intended as candidate evidence for human review, not automated legal citations.
