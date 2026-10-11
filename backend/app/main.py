import os
import shutil
import uuid
import time
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import (
    YOLO_MODEL_PATH,
    DEVICE,
    DEFAULT_CONFIDENCE,
    DEFAULT_SAMPLE_STRIDE,
    MAX_IMAGE_SIZE_BYTES,
    MAX_IMAGE_SIZE_MB,
    MAX_VIDEO_SIZE_BYTES,
    MAX_VIDEO_SIZE_MB,
    SUPPORTED_IMAGE_EXTENSIONS,
    SUPPORTED_VIDEO_EXTENSIONS,
    UPLOADS_DIR,
    PROCESSED_DIR,
    REPORTS_DIR,
    EVIDENCE_DIR,
    SAMPLES_DIR,
)
from .schemas import (
    HealthResponse,
    ImageAnalysisResponse,
    VideoJobStatus,
    VideoJobResult,
    AnalysisConfig,
    LaneDefinition,
    CountingLineDefinition,
    VehicleSummary,
    AnalysisRecordSummary,
)
from .database import (
    init_db,
    create_analysis_record,
    update_analysis_progress,
    complete_analysis_record,
    fail_analysis_record,
    get_analysis_by_id,
    get_all_analyses,
    delete_analysis_by_id,
    get_events_for_analysis,
)
from .detector import DetectorService
from .congestion import CongestionAnalyzer
from .video_processor import VideoProcessor
from .reports import generate_reports

SERVER_START_TIME = time.time()
detector_service: Optional[DetectorService] = None
video_processor: Optional[VideoProcessor] = None


def get_detector() -> DetectorService:
    global detector_service, video_processor
    if detector_service is None:
        detector_service = DetectorService(model_path=YOLO_MODEL_PATH, device=DEVICE)
        video_processor = VideoProcessor(detector=detector_service)
    return detector_service


def get_video_processor() -> VideoProcessor:
    global video_processor
    if video_processor is None:
        get_detector()
    return video_processor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema
    init_db()
    # Eagerly load model on startup
    try:
        get_detector()
    except Exception as e:
        print(f"Startup Warning: Could not initialize YOLO model: {e}")
    yield


app = FastAPI(
    title="Indian Traffic Intelligence API",
    description="Locally Runnable Computer Vision & Multi-Object Tracking Engine for Traffic Analytics",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration for Vite and local clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static file mounts
app.mount("/static/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")
app.mount("/static/processed", StaticFiles(directory=str(PROCESSED_DIR)), name="processed")
app.mount("/static/evidence", StaticFiles(directory=str(EVIDENCE_DIR)), name="evidence")
app.mount("/static/samples", StaticFiles(directory=str(SAMPLES_DIR)), name="samples")


def sanitize_filename(filename: str) -> str:
    """Protects against path traversal attacks by extracting base filename."""
    return Path(filename).name


def parse_analysis_config(
    direction: Optional[str] = "down",
    road_roi: Optional[str] = None,
    lanes_json: Optional[str] = None,
    counting_lines_json: Optional[str] = None,
    restricted_zones_json: Optional[str] = None,
    confidence: float = DEFAULT_CONFIDENCE,
    sample_stride: int = DEFAULT_SAMPLE_STRIDE,
) -> AnalysisConfig:
    """Safely deserializes and validates analysis configuration options."""
    cfg = AnalysisConfig(
        expected_direction=direction or "down",
        confidence_threshold=max(0.05, min(0.95, confidence)),
        sample_stride=max(1, min(10, sample_stride)),
    )

    if road_roi:
        try:
            parsed = json.loads(road_roi)
            if isinstance(parsed, list) and len(parsed) == 4:
                cfg.road_roi = [float(x) for x in parsed]
        except Exception:
            pass

    if lanes_json:
        try:
            parsed_lanes = json.loads(lanes_json)
            if isinstance(parsed_lanes, list):
                for item in parsed_lanes:
                    if isinstance(item, dict) and "bounds" in item and len(item["bounds"]) == 4:
                        cfg.lanes.append(
                            LaneDefinition(
                                id=item.get("id", str(uuid.uuid4())[:6]),
                                name=item.get("name", "Lane"),
                                bounds=[float(b) for b in item["bounds"]],
                                permitted_direction=item.get("permitted_direction", direction or "down"),
                                permitted_classes=item.get("permitted_classes"),
                            )
                        )
        except Exception:
            pass

    if counting_lines_json:
        try:
            parsed_lines = json.loads(counting_lines_json)
            if isinstance(parsed_lines, list):
                for item in parsed_lines:
                    if isinstance(item, dict) and "coords" in item and len(item["coords"]) == 4:
                        cfg.counting_lines.append(
                            CountingLineDefinition(
                                id=item.get("id", str(uuid.uuid4())[:6]),
                                name=item.get("name", "Counting Line"),
                                coords=[float(c) for c in item["coords"]],
                                direction_check=item.get("direction_check", "both"),
                            )
                        )
        except Exception:
            pass

    if restricted_zones_json:
        try:
            parsed_rz = json.loads(restricted_zones_json)
            if isinstance(parsed_rz, list):
                for zone in parsed_rz:
                    if isinstance(zone, list) and len(zone) == 4:
                        cfg.restricted_zones.append([float(z) for z in zone])
        except Exception:
            pass

    return cfg


@app.get("/api/health", response_model=HealthResponse)
def get_health():
    """System health, model readiness, hardware device, and supported class list."""
    try:
        det = get_detector()
        is_ready = det is not None and det.model is not None
    except Exception:
        is_ready = False

    classes_supported = ["Car", "Motorcycle", "Bus", "Truck", "Bicycle", "Pedestrian"]
    unverified_classes = ["Auto-rickshaw (requires dedicated Indian driving dataset fine-tuned model)"]

    return HealthResponse(
        status="healthy" if is_ready else "initializing",
        ready=is_ready,
        model_name=str(Path(YOLO_MODEL_PATH).name),
        device=DEVICE,
        classes_supported=classes_supported,
        unverified_classes=unverified_classes,
        version="2.0.0",
        uptime_seconds=round(time.time() - SERVER_START_TIME, 1),
    )


@app.post("/api/analyze/image", response_model=ImageAnalysisResponse)
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
    direction: Optional[str] = Form("down"),
    road_roi: Optional[str] = Form(None),
    lane_config: Optional[str] = Form(None),
    counting_lines: Optional[str] = Form(None),
    restricted_zones: Optional[str] = Form(None),
):
    """
    Performs real YOLO detection on an uploaded still image.
    Validates file integrity by decoding bytes, enforces size limits, and generates reports.
    """
    det = get_detector()
    safe_name = sanitize_filename(file.filename or "image.jpg")
    ext = Path(safe_name).suffix.lower()

    if ext not in SUPPORTED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported image format '{ext}'. Allowed: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image size exceeds maximum {MAX_IMAGE_SIZE_MB}MB limit.",
        )

    # Decode bytes with OpenCV to ensure media is not corrupted
    nparr = np.frombuffer(content, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img_bgr is None or img_bgr.size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Corrupted or invalid image data. OpenCV failed to decode file.",
        )

    h, w = img_bgr.shape[:2]
    analysis_id = str(uuid.uuid4())[:8]

    # Save original image
    raw_filename = f"{analysis_id}_{safe_name}"
    raw_path = UPLOADS_DIR / raw_filename
    with open(raw_path, "wb") as f:
        f.write(content)

    cfg = parse_analysis_config(
        direction=direction,
        road_roi=road_roi,
        lanes_json=lane_config,
        counting_lines_json=counting_lines,
        restricted_zones_json=restricted_zones,
        confidence=confidence,
    )

    t0 = time.time()
    detections = det.detect_image(img_bgr, confidence_threshold=cfg.confidence_threshold)
    class_counts, total_vehicles, total_pedestrians = det.aggregate_class_counts(detections)
    proc_time = round(time.time() - t0, 3)

    # Congestion & Pedestrian metrics
    congestion_metrics = CongestionAnalyzer.calculate_congestion(
        detections=detections,
        img_w=w,
        img_h=h,
        road_roi=cfg.road_roi,
    )
    ped_metrics = CongestionAnalyzer.calculate_pedestrian_density(
        detections=detections,
        img_w=w,
        img_h=h,
    )

    # Annotate image
    annotated_img = det.annotate_image(
        image=img_bgr,
        detections=detections,
        road_roi=cfg.road_roi,
        lanes=cfg.lanes,
        counting_lines=cfg.counting_lines,
    )
    annotated_filename = f"annotated_{analysis_id}.jpg"
    annotated_path = PROCESSED_DIR / annotated_filename
    cv2.imwrite(str(annotated_path), annotated_img)

    riders_count = sum(1 for d in detections if d.is_rider)
    ped_metrics.riders_excluded_count = riders_count
    unique_by_class: Dict[str, int] = {cc.class_name: cc.count for cc in class_counts if cc.class_name not in ("Pedestrian", "Rider")}
    v_summary = VehicleSummary(
        unique_vehicles_total=total_vehicles,
        unique_vehicles_by_class=unique_by_class,
        vehicles_per_frame_peak=total_vehicles,
        vehicles_per_frame_avg=float(total_vehicles),
        total_frame_detections=len(detections),
        counting_line_results=[],
        riders_associated_count=riders_count,
    )

    limitations = [
        "Still image direction analysis is inconclusive: single-frame detection cannot determine vehicle trajectory or velocity without temporal multi-frame tracking.",
        "Counting lines require video motion tracking to observe line intersection across consecutive frames.",
        "Auto-rickshaws may be recognized as standard vehicles (Car, Motorcycle, Bus) under COCO weights.",
    ]
    warnings = [
        "Direction & wrong-side violations are not evaluated for still images to prevent unverified false positives.",
    ]

    response_data = {
        "analysis_id": analysis_id,
        "media_type": "image",
        "status": "completed",
        "filename": safe_name,
        "processing_time_seconds": proc_time,
        "image_width": w,
        "image_height": h,
        "vehicle_summary": v_summary.model_dump(),
        "total_pedestrians": total_pedestrians,
        "class_counts": [cc.model_dump() for cc in class_counts],
        "detections": [d.model_dump() for d in detections],
        "congestion": congestion_metrics.model_dump(),
        "pedestrian_metrics": ped_metrics.model_dump(),
        "events": [],
        "warnings": warnings,
        "limitations": limitations,
        "annotated_media_url": f"/static/processed/{annotated_filename}",
        "original_media_url": f"/static/uploads/{raw_filename}",
        "report_pdf_url": f"/api/reports/{analysis_id}/pdf",
        "report_csv_url": f"/api/reports/{analysis_id}/csv",
    }

    # Generate CSV & PDF reports
    generate_reports(analysis_id, response_data, REPORTS_DIR)

    # Persist in SQLite
    create_analysis_record(
        analysis_id=analysis_id,
        filename=safe_name,
        media_type="image",
        status="completed",
        message="Image analysis complete",
    )
    complete_analysis_record(analysis_id=analysis_id, result_data=response_data, events=[])

    return ImageAnalysisResponse(**response_data)


def _async_video_worker(
    analysis_id: str,
    video_path: Path,
    output_video_path: Path,
    cfg: AnalysisConfig,
):
    """Background worker thread for processing video jobs."""
    try:
        vp = get_video_processor()
        update_analysis_progress(
            analysis_id=analysis_id,
            status="processing",
            progress_percent=1,
            message="Validating video stream and initializing multi-object tracker...",
        )

        def progress_cb(pct: int, msg: str):
            update_analysis_progress(
                analysis_id=analysis_id,
                status="processing",
                progress_percent=pct,
                message=msg,
            )

        result_dict = vp.process_video(
            analysis_id=analysis_id,
            video_path=video_path,
            output_video_path=output_video_path,
            config=cfg,
            progress_callback=progress_cb,
        )

        # Generate reports
        generate_reports(analysis_id, result_dict, REPORTS_DIR)

        # Save to SQLite
        events_dicts = [e.model_dump() if hasattr(e, "model_dump") else e for e in result_dict.get("events", [])]
        complete_analysis_record(analysis_id=analysis_id, result_data=result_dict, events=events_dicts)

    except Exception as e:
        print(f"Error in video worker for analysis {analysis_id}: {e}")
        fail_analysis_record(analysis_id=analysis_id, error_message=str(e))


@app.post("/api/analyze/video")
async def analyze_video_endpoint(
    file: UploadFile = File(...),
    confidence: float = Form(0.25),
    sample_stride: int = Form(2),
    direction: Optional[str] = Form("down"),
    road_roi: Optional[str] = Form(None),
    lane_config: Optional[str] = Form(None),
    counting_lines: Optional[str] = Form(None),
    restricted_zones: Optional[str] = Form(None),
):
    """
    Creates an asynchronous video tracking and traffic intelligence analysis job.
    Validates video header, returns immediately with job_id for frontend polling.
    """
    safe_name = sanitize_filename(file.filename or "video.mp4")
    ext = Path(safe_name).suffix.lower()

    if ext not in SUPPORTED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported video format '{ext}'. Allowed: {', '.join(sorted(SUPPORTED_VIDEO_EXTENSIONS))}",
        )

    content = await file.read()
    if len(content) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Video file exceeds {MAX_VIDEO_SIZE_MB}MB size limit.",
        )

    job_id = str(uuid.uuid4())[:8]
    raw_video_filename = f"{job_id}_{safe_name}"
    upload_path = UPLOADS_DIR / raw_video_filename

    with open(upload_path, "wb") as f:
        f.write(content)

    # Validate video readability
    try:
        VideoProcessor.validate_video(upload_path)
    except Exception as e:
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupted video file: {str(e)}",
        )

    output_video_filename = f"annotated_{job_id}.mp4"
    output_video_path = PROCESSED_DIR / output_video_filename

    cfg = parse_analysis_config(
        direction=direction,
        road_roi=road_roi,
        lanes_json=lane_config,
        counting_lines_json=counting_lines,
        restricted_zones_json=restricted_zones,
        confidence=confidence,
        sample_stride=sample_stride,
    )

    create_analysis_record(
        analysis_id=job_id,
        filename=safe_name,
        media_type="video",
        status="queued",
        message="Job queued for processing",
    )

    # Launch background thread
    thread = threading.Thread(
        target=_async_video_worker,
        args=(job_id, upload_path, output_video_path, cfg),
        daemon=True,
    )
    thread.start()

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Video analysis job registered. Monitor /api/jobs/{job_id} for progress updates.",
    }


@app.get("/api/jobs/{job_id}", response_model=VideoJobStatus)
def get_job_status(job_id: str):
    """Retrieves real-time processing status and results for a background video job."""
    record = get_analysis_by_id(job_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job #{job_id} not found.")

    res_obj = None
    if record.get("result"):
        try:
            res_obj = VideoJobResult(**record["result"])
        except Exception as e:
            print(f"Error parsing VideoJobResult: {e}")

    return VideoJobStatus(
        job_id=record["id"],
        status=record["status"],
        progress_percent=record.get("progress_percent", 0),
        message=record.get("message", ""),
        created_at=record["created_at"],
        updated_at=record.get("completed_at") or record["created_at"],
        error=record.get("error"),
        result=res_obj,
    )


@app.get("/api/results/{analysis_id}")
def get_analysis_result(analysis_id: str):
    """Retrieves the full analysis data and events for an image or completed video."""
    record = get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Analysis #{analysis_id} not found.")

    events = get_events_for_analysis(analysis_id)
    return {
        "record": record,
        "events": events,
        "result": record.get("result"),
    }


@app.get("/api/history")
def get_history(limit: int = 50):
    """Returns persistent analysis history stored in SQLite."""
    items = get_all_analyses(limit=limit)
    return {"history": items}


@app.delete("/api/history/{analysis_id}")
def delete_history_item(analysis_id: str):
    """Deletes analysis record and associated event records."""
    deleted = delete_analysis_by_id(analysis_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")
    return {"success": True, "message": f"Analysis #{analysis_id} deleted."}


@app.get("/api/reports/{analysis_id}/pdf")
def get_pdf_report(analysis_id: str):
    """Streams or downloads the ReportLab generated PDF report."""
    pdf_path = REPORTS_DIR / f"traffic_report_{analysis_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PDF report not found for this analysis.")
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"indian_traffic_report_{analysis_id}.pdf",
    )


@app.get("/api/reports/{analysis_id}/csv")
def get_csv_report(analysis_id: str):
    """Streams or downloads the structured CSV metrics report."""
    csv_path = REPORTS_DIR / f"traffic_report_{analysis_id}.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="CSV report not found for this analysis.")
    return FileResponse(
        path=str(csv_path),
        media_type="text/csv",
        filename=f"indian_traffic_report_{analysis_id}.csv",
    )


@app.get("/api/samples")
def list_sample_media():
    """Lists pre-packaged sample traffic images and videos available locally."""
    samples = []
    if SAMPLES_DIR.exists():
        for p in SAMPLES_DIR.iterdir():
            if p.is_file():
                ext = p.suffix.lower()
                is_video = ext in SUPPORTED_VIDEO_EXTENSIONS
                is_image = ext in SUPPORTED_IMAGE_EXTENSIONS
                if is_video or is_image:
                    samples.append({
                        "name": p.name,
                        "type": "video" if is_video else "image",
                        "size_bytes": p.stat().st_size,
                        "url": f"/static/samples/{p.name}",
                    })
    return {"samples": samples}


@app.post("/api/analyze/sample")
def analyze_sample_media(
    sample_name: str = Form(...),
    confidence: float = Form(0.25),
    direction: Optional[str] = Form("down"),
    sample_stride: int = Form(2),
    road_roi: Optional[str] = Form(None),
    lane_config: Optional[str] = Form(None),
    counting_lines: Optional[str] = Form(None),
    restricted_zones: Optional[str] = Form(None),
):
    """
    Executes analysis directly on a sample file in the samples/ folder without re-uploading.
    """
    sample_path = SAMPLES_DIR / sanitize_filename(sample_name)
    if not sample_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sample file '{sample_name}' not found.")

    ext = sample_path.suffix.lower()
    is_video = ext in SUPPORTED_VIDEO_EXTENSIONS
    is_image = ext in SUPPORTED_IMAGE_EXTENSIONS

    if not is_video and not is_image:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported sample format.")

    job_id = str(uuid.uuid4())[:8]

    if is_image:
        img_bgr = cv2.imread(str(sample_path))
        if img_bgr is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to read sample image.")

        h, w = img_bgr.shape[:2]
        det = get_detector()
        cfg = parse_analysis_config(
            direction=direction,
            road_roi=road_roi,
            lanes_json=lane_config,
            counting_lines_json=counting_lines,
            restricted_zones_json=restricted_zones,
            confidence=confidence,
        )

        t0 = time.time()
        detections = det.detect_image(img_bgr, confidence_threshold=cfg.confidence_threshold)
        class_counts, total_vehicles, total_pedestrians = det.aggregate_class_counts(detections)
        proc_time = round(time.time() - t0, 3)

        congestion_metrics = CongestionAnalyzer.calculate_congestion(detections, w, h, road_roi=cfg.road_roi)
        ped_metrics = CongestionAnalyzer.calculate_pedestrian_density(detections, w, h)

        annotated_img = det.annotate_image(img_bgr, detections, road_roi=cfg.road_roi, lanes=cfg.lanes, counting_lines=cfg.counting_lines)
        annotated_filename = f"annotated_{job_id}.jpg"
        annotated_path = PROCESSED_DIR / annotated_filename
        cv2.imwrite(str(annotated_path), annotated_img)

        # Copy sample into uploads
        upload_path = UPLOADS_DIR / f"{job_id}_{sample_path.name}"
        shutil.copyfile(sample_path, upload_path)

        riders_count = sum(1 for d in detections if d.is_rider)
        ped_metrics.riders_excluded_count = riders_count
        unique_by_class = {cc.class_name: cc.count for cc in class_counts if cc.class_name not in ("Pedestrian", "Rider")}
        v_summary = VehicleSummary(
            unique_vehicles_total=total_vehicles,
            unique_vehicles_by_class=unique_by_class,
            vehicles_per_frame_peak=total_vehicles,
            vehicles_per_frame_avg=float(total_vehicles),
            total_frame_detections=len(detections),
            counting_line_results=[],
            riders_associated_count=riders_count,
        )

        response_data = {
            "analysis_id": job_id,
            "media_type": "image",
            "status": "completed",
            "filename": sample_path.name,
            "processing_time_seconds": proc_time,
            "image_width": w,
            "image_height": h,
            "vehicle_summary": v_summary.model_dump(),
            "total_pedestrians": total_pedestrians,
            "class_counts": [cc.model_dump() for cc in class_counts],
            "detections": [d.model_dump() for d in detections],
            "congestion": congestion_metrics.model_dump(),
            "pedestrian_metrics": ped_metrics.model_dump(),
            "events": [],
            "warnings": ["Still image direction analysis is inconclusive without temporal tracking."],
            "limitations": ["Pretrained COCO weights may map auto-rickshaws to cars or motorcycles."],
            "annotated_media_url": f"/static/processed/{annotated_filename}",
            "original_media_url": f"/static/uploads/{upload_path.name}",
            "report_pdf_url": f"/api/reports/{job_id}/pdf",
            "report_csv_url": f"/api/reports/{job_id}/csv",
        }

        generate_reports(job_id, response_data, REPORTS_DIR)
        create_analysis_record(analysis_id=job_id, filename=sample_path.name, media_type="image", status="completed", message="Sample image analysis complete")
        complete_analysis_record(analysis_id=job_id, result_data=response_data, events=[])

        return response_data

    else:
        # Video sample
        upload_path = UPLOADS_DIR / f"{job_id}_{sample_path.name}"
        shutil.copyfile(sample_path, upload_path)
        output_video_path = PROCESSED_DIR / f"annotated_{job_id}.mp4"

        cfg = parse_analysis_config(
            direction=direction,
            road_roi=road_roi,
            lanes_json=lane_config,
            counting_lines_json=counting_lines,
            restricted_zones_json=restricted_zones,
            confidence=confidence,
            sample_stride=sample_stride,
        )

        create_analysis_record(
            analysis_id=job_id,
            filename=sample_path.name,
            media_type="video",
            status="queued",
            message="Sample video queued for analysis",
        )

        thread = threading.Thread(
            target=_async_video_worker,
            args=(job_id, upload_path, output_video_path, cfg),
            daemon=True,
        )
        thread.start()

        return {
            "job_id": job_id,
            "status": "queued",
            "message": f"Sample video analysis queued. Monitor /api/jobs/{job_id}.",
        }
