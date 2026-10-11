from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    class_name: str
    model_class_id: int
    track_id: Optional[int] = None
    frame_number: Optional[int] = None
    timestamp_seconds: Optional[float] = None
    is_rider: bool = False
    associated_vehicle: Optional[str] = None


class ClassCount(BaseModel):
    class_name: str
    count: int
    percentage: float


class LaneDefinition(BaseModel):
    id: str
    name: str
    bounds: List[float] = Field(
        ...,
        description="[x_min, y_min, x_max, y_max] normalized coordinates (0.0 to 1.0)",
    )
    permitted_direction: str = "down"  # "down", "up", "left", "right", "bidirectional"
    permitted_classes: Optional[List[str]] = None


class CountingLineDefinition(BaseModel):
    id: str
    name: str
    # Line segment [x1, y1, x2, y2] normalized (0.0 to 1.0)
    coords: List[float]
    direction_check: str = "both"  # "forward", "reverse", "both"


class AnalysisConfig(BaseModel):
    expected_direction: str = "down"  # "down", "up", "left", "right"
    road_roi: Optional[List[float]] = None  # [x_min, y_min, x_max, y_max] normalized
    lanes: List[LaneDefinition] = []
    counting_lines: List[CountingLineDefinition] = []
    restricted_zones: List[List[float]] = []  # List of [x1, y1, x2, y2] normalized
    confidence_threshold: float = 0.25
    sample_stride: int = 2
    min_displacement_px: float = 25.0
    min_observation_frames: int = 5


class CongestionMetrics(BaseModel):
    level: str  # "Low", "Moderate", "High"
    score: float  # 0.0 to 1.0
    vehicle_count: int
    occupancy_ratio: float
    avg_speed_px_per_sec: Optional[float] = None
    description: str
    methodology_note: str


class PedestrianMetrics(BaseModel):
    count: int
    unique_count: Optional[int] = None
    density_level: str  # "Low", "Moderate", "High"
    density_score: float
    in_crossing_zone_count: int = 0
    riders_excluded_count: int = 0
    description: str
    limitations_note: str


class CountingLineResult(BaseModel):
    line_id: str
    line_name: str
    forward_count: int
    reverse_count: int
    total_crossings: int


class TrafficEvent(BaseModel):
    id: str
    event_type: str  # "wrong_side", "lane_violation", "restricted_entry", "stopped_vehicle", "density_spike"
    severity: str  # "warning", "critical", "info"
    description: str
    timestamp_seconds: float
    frame_number: int
    track_id: Optional[int] = None
    vehicle_type: Optional[str] = None
    rule_name: str
    reason: str
    evidence_url: Optional[str] = None


class VehicleSummary(BaseModel):
    unique_vehicles_total: int
    unique_vehicles_by_class: Dict[str, int]
    vehicles_per_frame_peak: int
    vehicles_per_frame_avg: float
    total_frame_detections: int
    counting_line_results: List[CountingLineResult] = []
    riders_associated_count: int = 0


class ImageAnalysisResponse(BaseModel):
    analysis_id: str
    media_type: str = "image"
    status: str = "completed"
    filename: str
    processing_time_seconds: float
    image_width: int
    image_height: int
    vehicle_summary: VehicleSummary
    total_pedestrians: int
    class_counts: List[ClassCount]
    detections: List[BoundingBox] = []
    congestion: CongestionMetrics
    pedestrian_metrics: PedestrianMetrics
    events: List[TrafficEvent] = []
    warnings: List[str] = []
    limitations: List[str] = []
    annotated_media_url: str
    original_media_url: str
    report_pdf_url: str
    report_csv_url: str


class VideoJobResult(BaseModel):
    analysis_id: str
    media_type: str = "video"
    filename: str
    processing_time_seconds: float
    video_width: int
    video_height: int
    fps: float
    total_frames: int
    frames_analyzed: int
    duration_seconds: float
    vehicle_summary: VehicleSummary
    total_pedestrians: int
    unique_pedestrians: int
    class_counts: List[ClassCount]
    congestion: CongestionMetrics
    pedestrian_metrics: PedestrianMetrics
    events: List[TrafficEvent] = []
    per_frame_timeline: List[Dict[str, Any]] = []
    warnings: List[str] = []
    limitations: List[str] = []
    annotated_media_url: str
    original_media_url: str
    report_pdf_url: str
    report_csv_url: str


class VideoJobStatus(BaseModel):
    job_id: str
    status: str  # "queued", "processing", "completed", "failed"
    progress_percent: int  # 0 to 100
    current_frame: int = 0
    total_frames: int = 0
    message: str
    created_at: str
    updated_at: str
    error: Optional[str] = None
    result: Optional[VideoJobResult] = None


class HealthResponse(BaseModel):
    status: str
    ready: bool
    model_name: str
    device: str
    classes_supported: List[str]
    unverified_classes: List[str]
    version: str
    uptime_seconds: float


class AnalysisRecordSummary(BaseModel):
    id: str
    filename: str
    media_type: str
    status: str
    created_at: str
    completed_at: Optional[str] = None
    total_vehicles: int
    total_pedestrians: int
    events_count: int
    congestion_level: str
    annotated_media_url: Optional[str] = None
