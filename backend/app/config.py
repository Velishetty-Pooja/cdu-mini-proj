import os
from pathlib import Path
from typing import Dict, List, Set

# Base Directories
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load environment variables from .env file if available
try:
    from dotenv import load_dotenv
    if (BACKEND_DIR / ".env").exists():
        load_dotenv(BACKEND_DIR / ".env")
    elif (PROJECT_ROOT / ".env").exists():
        load_dotenv(PROJECT_ROOT / ".env")
    else:
        load_dotenv()
except ImportError:
    pass

STORAGE_DIR = Path(os.getenv("STORAGE_DIR", str(BACKEND_DIR / "storage")))
UPLOADS_DIR = STORAGE_DIR / "uploads"
PROCESSED_DIR = STORAGE_DIR / "processed"
REPORTS_DIR = STORAGE_DIR / "reports"
EVIDENCE_DIR = STORAGE_DIR / "evidence"
SAMPLES_DIR = Path(os.getenv("SAMPLES_DIR", str(BACKEND_DIR / "samples")))

# Ensure directories exist
for directory in [UPLOADS_DIR, PROCESSED_DIR, REPORTS_DIR, EVIDENCE_DIR, SAMPLES_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_PATH = STORAGE_DIR / "traffic_intelligence.db"

# YOLO Model Configuration
# Check if weights exist locally in backend dir or app dir, else ultralytics will auto-download
DEFAULT_MODEL_LOCAL = BACKEND_DIR / "yolov8n.pt"
YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", str(DEFAULT_MODEL_LOCAL if DEFAULT_MODEL_LOCAL.exists() else "yolov8n.pt"))
DEVICE = os.getenv("DEVICE", "cpu")  # "cpu", "cuda", "mps"

# Detection Defaults
DEFAULT_CONFIDENCE = float(os.getenv("DEFAULT_CONFIDENCE", "0.25"))
DEFAULT_IOU = float(os.getenv("DEFAULT_IOU", "0.45"))
DEFAULT_SAMPLE_STRIDE = int(os.getenv("DEFAULT_SAMPLE_STRIDE", "2"))

# COCO Dataset Traffic Class Mapping
# Real COCO classes: 0=person, 1=bicycle, 2=car, 3=motorcycle, 5=bus, 7=truck
COCO_CLASS_MAP: Dict[int, str] = {
    0: "Pedestrian",
    1: "Bicycle",
    2: "Car",
    3: "Motorcycle",
    5: "Bus",
    7: "Truck",
}

# Supported Vehicle Classes (distinguished from Pedestrians)
SUPPORTED_VEHICLE_CLASSES: Set[str] = {
    "Car",
    "Motorcycle",
    "Bus",
    "Truck",
    "Bicycle",
    "Auto-rickshaw",  # Documented: supported via custom Indian dataset models
}

PEDESTRIAN_CLASSES: Set[str] = {"Pedestrian"}

# Upload Restrictions
MAX_IMAGE_SIZE_MB = int(os.getenv("MAX_IMAGE_SIZE_MB", "25"))
MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "150"))
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# Wrong-side analysis defaults
DEFAULT_MIN_DISPLACEMENT_PX = 25.0
DEFAULT_MIN_OBSERVATION_FRAMES = 5
DEFAULT_WRONG_SIDE_COSINE_THRESHOLD = -0.30

# Congestion thresholds
CONGESTION_LOW_THRESHOLD = 0.20       # < 20% road occupancy
CONGESTION_MODERATE_THRESHOLD = 0.45  # 20% - 45% occupancy
# > 45% occupancy is High Congestion
