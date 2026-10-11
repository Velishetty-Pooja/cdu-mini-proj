import pytest
from app.schemas import (
    BoundingBox,
    ClassCount,
    CongestionMetrics,
    PedestrianMetrics,
    TrafficEvent,
    VehicleSummary,
    ImageAnalysisResponse,
)
from app.detector import DetectorService


def test_bounding_box_schema():
    box = BoundingBox(
        x1=100.5,
        y1=50.2,
        x2=250.0,
        y2=200.0,
        confidence=0.885,
        class_name="Car",
        model_class_id=2,
    )
    assert box.x1 == 100.5
    assert box.class_name == "Car"
    assert box.model_class_id == 2
    assert box.confidence == 0.885


def test_image_analysis_response_schema():
    v_summary = VehicleSummary(
        unique_vehicles_total=2,
        unique_vehicles_by_class={"Car": 2},
        vehicles_per_frame_peak=2,
        vehicles_per_frame_avg=2.0,
        total_frame_detections=2,
        counting_line_results=[],
    )
    congestion = CongestionMetrics(
        level="Low",
        score=0.15,
        vehicle_count=2,
        occupancy_ratio=0.12,
        description="Light traffic flow",
        methodology_note="Area coverage",
    )
    ped = PedestrianMetrics(
        count=0,
        density_level="Low",
        density_score=0.0,
        description="No pedestrians",
        limitations_note="Limitations apply",
    )
    resp = ImageAnalysisResponse(
        analysis_id="test-123",
        media_type="image",
        status="completed",
        filename="road.jpg",
        processing_time_seconds=0.045,
        image_width=640,
        image_height=480,
        vehicle_summary=v_summary,
        total_pedestrians=0,
        class_counts=[ClassCount(class_name="Car", count=2, percentage=100.0)],
        detections=[],
        congestion=congestion,
        pedestrian_metrics=ped,
        events=[],
        warnings=[],
        limitations=[],
        annotated_media_url="/static/processed/annotated_test.jpg",
        original_media_url="/static/uploads/road.jpg",
        report_pdf_url="/api/reports/test-123/pdf",
        report_csv_url="/api/reports/test-123/csv",
    )
    assert resp.analysis_id == "test-123"
    assert resp.vehicle_summary.unique_vehicles_total == 2
    assert resp.congestion.level == "Low"


def test_missing_model_weights_explicit_error():
    """Verifies that non-existent model weights raise an explicit actionable error without substituting dummy predictions."""
    with pytest.raises((FileNotFoundError, RuntimeError)) as exc_info:
        DetectorService(model_path="non_existent_weights_xyz123.bin")
    err_msg = str(exc_info.value)
    assert "not found" in err_msg or "Failed to load" in err_msg
