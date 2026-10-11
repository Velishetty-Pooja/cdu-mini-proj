from pathlib import Path
from app.reports import generate_csv_report, generate_pdf_report
from app.schemas import ClassCount, CongestionMetrics, TrafficEvent


def test_csv_report_generation(tmp_path: Path):
    analysis_id = "test_csv_123"
    csv_file = tmp_path / f"traffic_report_{analysis_id}.csv"

    sample_data = {
        "analysis_id": analysis_id,
        "media_type": "image",
        "filename": "junction.jpg",
        "processing_time_seconds": 0.12,
        "total_pedestrians": 1,
        "vehicle_summary": {
            "unique_vehicles_total": 5,
            "vehicles_per_frame_peak": 5,
            "vehicles_per_frame_avg": 5.0,
            "total_frame_detections": 5,
            "counting_line_results": [],
        },
        "congestion": {
            "level": "Moderate",
            "occupancy_ratio": 0.32,
        },
        "class_counts": [
            {"class_name": "Car", "count": 3, "percentage": 60.0},
            {"class_name": "Motorcycle", "count": 2, "percentage": 40.0},
        ],
        "events": [
            {
                "id": "EV-1",
                "timestamp_seconds": 1.2,
                "frame_number": 12,
                "event_type": "wrong_side",
                "severity": "critical",
                "track_id": 4,
                "vehicle_type": "Car",
                "rule_name": "Direction",
                "reason": "Observed movement against flow",
            }
        ],
        "limitations": ["Pretrained COCO weights."],
    }

    generated_path = generate_csv_report(analysis_id, sample_data, csv_file)
    assert generated_path.exists()
    content = generated_path.read_text(encoding="utf-8")
    assert "INDIAN TRAFFIC INTELLIGENCE SYSTEM ANALYSIS REPORT" in content
    assert "test_csv_123" in content
    assert "Car,3,60.0" in content
    assert "EV-1" in content


def test_pdf_report_generation(tmp_path: Path):
    analysis_id = "test_pdf_456"
    pdf_file = tmp_path / f"traffic_report_{analysis_id}.pdf"

    sample_data = {
        "analysis_id": analysis_id,
        "media_type": "video",
        "filename": "highway.mp4",
        "processing_time_seconds": 2.45,
        "total_pedestrians": 0,
        "vehicle_summary": {
            "unique_vehicles_total": 8,
            "vehicles_per_frame_peak": 4,
            "vehicles_per_frame_avg": 3.2,
            "total_frame_detections": 24,
            "counting_line_results": [],
        },
        "congestion": {
            "level": "Low",
            "occupancy_ratio": 0.14,
        },
        "class_counts": [
            {"class_name": "Car", "count": 5, "percentage": 62.5},
            {"class_name": "Truck", "count": 3, "percentage": 37.5},
        ],
        "events": [],
        "limitations": ["Camera calibration limitation."],
    }

    generated_path = generate_pdf_report(analysis_id, sample_data, pdf_file)
    assert generated_path.exists()
    # Verify PDF magic number (%PDF-)
    with open(generated_path, "rb") as f:
        header = f.read(5)
    assert header == b"%PDF-"
    assert generated_path.stat().st_size > 1000  # Non-empty, valid document size


def test_vehicle_summary_attribute_access_regression(tmp_path: Path):
    """
    REGRESSION TEST: Ensures that passing raw Pydantic instances (such as VehicleSummary)
    to database completion and report generation does NOT raise:
    'VehicleSummary' object has no attribute 'get'.
    """
    from app.schemas import VehicleSummary, CongestionMetrics, PedestrianMetrics, TrafficEvent
    from app.database import create_analysis_record, complete_analysis_record, get_analysis_by_id

    analysis_id = "reg_test_veh_summary"
    create_analysis_record(
        analysis_id=analysis_id,
        filename="highway_test.mp4",
        media_type="video",
        status="queued",
    )

    # Real Pydantic instances (NOT dicts)
    pydantic_veh_summary = VehicleSummary(
        unique_vehicles_total=12,
        unique_vehicles_by_class={"Car": 8, "Truck": 4},
        vehicles_per_frame_peak=6,
        vehicles_per_frame_avg=4.5,
        total_frame_detections=120,
        counting_line_results=[],
        riders_associated_count=2,
    )

    pydantic_congestion = CongestionMetrics(
        level="Moderate",
        score=0.35,
        vehicle_count=12,
        occupancy_ratio=0.35,
        description="Moderate traffic density observed",
        methodology_note="Spatial bounding box occupancy calculation",
    )

    pydantic_ped = PedestrianMetrics(
        count=3,
        unique_count=3,
        density_level="Low",
        density_score=0.3,
        in_crossing_zone_count=3,
        riders_excluded_count=2,
        description="3 pedestrians tracked",
        limitations_note="Standard detection limits",
    )

    pydantic_event = TrafficEvent(
        id=f"EV-{analysis_id}-1",
        event_type="wrong_side",
        severity="critical",
        description="Opposite direction movement detected",
        timestamp_seconds=2.4,
        frame_number=24,
        track_id=7,
        vehicle_type="Car",
        rule_name="Direction of Travel",
        reason="Trajectory cosine alignment < -0.30",
        evidence_url=None,
    )

    result_data_with_pydantic_models = {
        "analysis_id": analysis_id,
        "media_type": "video",
        "filename": "highway_test.mp4",
        "processing_time_seconds": 3.14,
        "video_width": 1280,
        "video_height": 720,
        "fps": 30.0,
        "total_frames": 150,
        "frames_analyzed": 75,
        "duration_seconds": 5.0,
        "vehicle_summary": pydantic_veh_summary,  # Raw Pydantic Model!
        "total_pedestrians": 3,
        "unique_pedestrians": 3,
        "class_counts": [
            ClassCount(class_name="Car", count=8, percentage=66.7),
            ClassCount(class_name="Truck", count=4, percentage=33.3),
        ],
        "congestion": pydantic_congestion,  # Raw Pydantic Model!
        "pedestrian_metrics": pydantic_ped,  # Raw Pydantic Model!
        "events": [pydantic_event],
        "warnings": [],
        "limitations": ["Calibrated camera parameters required for physical metric speeds."],
        "annotated_media_url": f"/static/processed/annotated_{analysis_id}.mp4",
        "original_media_url": f"/static/uploads/{analysis_id}_highway_test.mp4",
        "report_pdf_url": f"/api/reports/{analysis_id}/pdf",
        "report_csv_url": f"/api/reports/{analysis_id}/csv",
    }

    # 1. Verify complete_analysis_record handles raw Pydantic instances cleanly
    complete_analysis_record(
        analysis_id=analysis_id,
        result_data=result_data_with_pydantic_models,
        events=[pydantic_event.model_dump()],
    )

    record = get_analysis_by_id(analysis_id)
    assert record is not None
    assert record["status"] == "completed"
    assert record["total_vehicles"] == 12
    assert record["congestion_level"] == "Moderate"
    assert record["events_count"] == 1

    # 2. Verify PDF report generation handles raw Pydantic instances without throwing AttributeError
    pdf_path = tmp_path / f"test_{analysis_id}.pdf"
    generate_pdf_report(analysis_id, result_data_with_pydantic_models, pdf_path)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000

    # 3. Verify CSV report generation handles raw Pydantic instances without error
    csv_path = tmp_path / f"test_{analysis_id}.csv"
    generate_csv_report(analysis_id, result_data_with_pydantic_models, csv_path)
    assert csv_path.exists()
    assert csv_path.stat().st_size > 100
