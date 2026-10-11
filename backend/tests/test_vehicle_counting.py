from app.schemas import BoundingBox, CountingLineDefinition
from app.detector import DetectorService
from app.tracker import TrackingManager
from app.traffic_rules import TrafficRulesEngine


def test_image_vehicle_counting_and_pedestrian_separation():
    """Verifies that vehicles and pedestrians are separated and aggregated from synthetic detections."""
    detections = [
        BoundingBox(x1=10, y1=10, x2=50, y2=50, confidence=0.9, class_name="Car", model_class_id=2),
        BoundingBox(x1=60, y1=10, x2=90, y2=50, confidence=0.85, class_name="Car", model_class_id=2),
        BoundingBox(x1=100, y1=10, x2=130, y2=40, confidence=0.8, class_name="Motorcycle", model_class_id=3),
        BoundingBox(x1=140, y1=10, x2=180, y2=80, confidence=0.95, class_name="Bus", model_class_id=5),
        BoundingBox(x1=200, y1=10, x2=220, y2=60, confidence=0.75, class_name="Pedestrian", model_class_id=0),
        BoundingBox(x1=230, y1=10, x2=250, y2=60, confidence=0.78, class_name="Pedestrian", model_class_id=0),
    ]

    class_counts, total_vehicles, total_pedestrians = DetectorService.aggregate_class_counts(detections)

    assert total_vehicles == 4  # 2 Cars + 1 Motorcycle + 1 Bus
    assert total_pedestrians == 2  # 2 Pedestrians

    counts_dict = {c.class_name: c.count for c in class_counts}
    assert counts_dict["Car"] == 2
    assert counts_dict["Motorcycle"] == 1
    assert counts_dict["Bus"] == 1
    assert counts_dict["Pedestrian"] == 2


def test_video_persistent_unique_vehicle_aggregation():
    """Verifies that multiple frames observing the SAME track ID do not inflate vehicle counts."""
    mgr = TrackingManager()

    # Simulate Vehicle 1 (Car) seen across 10 consecutive frames
    for f in range(10):
        mgr.update_track(
            track_id=1,
            class_name="Car",
            bbox=(100.0, 50.0 + f * 5, 150.0, 100.0 + f * 5),
            confidence=0.9,
            frame_idx=f,
            timestamp_seconds=f * 0.1,
        )

    # Simulate Vehicle 2 (Truck) seen across 8 consecutive frames
    for f in range(2, 10):
        mgr.update_track(
            track_id=2,
            class_name="Truck",
            bbox=(200.0, 80.0 + f * 4, 270.0, 160.0 + f * 4),
            confidence=0.88,
            frame_idx=f,
            timestamp_seconds=f * 0.1,
        )

    # Simulate fleeting false positive (seen only once) - should be ignored by aggregation policy
    mgr.update_track(
        track_id=99,
        class_name="Car",
        bbox=(300.0, 300.0, 320.0, 320.0),
        confidence=0.3,
        frame_idx=4,
        timestamp_seconds=0.4,
    )

    unique_vehicles, counts_by_class, unique_peds = mgr.get_unique_vehicle_metrics()

    assert unique_vehicles == 2
    assert counts_by_class["Car"] == 1
    assert counts_by_class["Truck"] == 1
    assert unique_peds == 0


def test_virtual_counting_line_crossing():
    """Verifies that a vehicle crossing a virtual counting line is counted exactly once."""
    mgr = TrackingManager()
    counting_line = CountingLineDefinition(
        id="gate_1",
        name="Main Entry Gate",
        coords=[0.0, 0.5, 1.0, 0.5],  # Horizontal line across the middle (y=0.5 normalized)
        direction_check="both",
    )
    rules_engine = TrafficRulesEngine(
        counting_lines=[counting_line]
    )

    img_w, img_h = 640, 480
    # Gate y is at 240px

    # Frame 0: Vehicle at y=200 (above gate)
    e1 = mgr.update_track(1, "Car", (100, 160, 140, 200), 0.9, 0, 0.0)
    c0 = rules_engine.check_counting_lines(e1, img_w, img_h)
    assert len(c0) == 0

    # Frame 1: Vehicle crosses to y=260 (below gate)
    e1 = mgr.update_track(1, "Car", (100, 220, 140, 260), 0.9, 1, 0.1)
    c1 = rules_engine.check_counting_lines(e1, img_w, img_h)
    assert len(c1) == 1
    assert c1[0][0] == "gate_1"

    # Frame 2: Vehicle continues down to y=320 -> should NOT trigger duplicate count
    e1 = mgr.update_track(1, "Car", (100, 280, 140, 320), 0.9, 2, 0.2)
    c2 = rules_engine.check_counting_lines(e1, img_w, img_h)
    assert len(c2) == 0

    results = rules_engine.get_counting_line_results()
    assert len(results) == 1
    assert results[0].total_crossings == 1


def test_rider_motorcycle_association():
    """
    Verifies that a person seated on a motorcycle is correctly associated as a rider
    and NOT counted as an independent pedestrian.
    """
    # Motorcycle located at [100, 150, 180, 260]
    bike = BoundingBox(x1=100, y1=150, x2=180, y2=260, confidence=0.88, class_name="Motorcycle", model_class_id=3)
    # Person seated on the motorcycle: [110, 120, 160, 220]
    rider_person = BoundingBox(x1=110, y1=120, x2=160, y2=220, confidence=0.82, class_name="Pedestrian", model_class_id=0)
    # Independent pedestrian walking on sidewalk: [300, 120, 340, 220]
    walking_ped = BoundingBox(x1=300, y1=120, x2=340, y2=220, confidence=0.79, class_name="Pedestrian", model_class_id=0)

    detections = [bike, rider_person, walking_ped]
    DetectorService.associate_riders(detections)

    assert rider_person.is_rider is True
    assert rider_person.associated_vehicle == "Motorcycle"
    assert walking_ped.is_rider is False
    assert walking_ped.associated_vehicle is None

    class_counts, total_vehicles, total_pedestrians = DetectorService.aggregate_class_counts(detections)
    assert total_vehicles == 1  # 1 Motorcycle
    assert total_pedestrians == 1  # 1 genuine pedestrian on sidewalk (rider excluded)
    counts_map = {c.class_name: c.count for c in class_counts}
    assert counts_map.get("Rider") == 1
    assert counts_map.get("Pedestrian") == 1
    assert counts_map.get("Motorcycle") == 1


def test_tracking_manager_rider_exclusion():
    """Verifies that TrackedEntity instances marked as riders are not counted in unique_pedestrians."""
    mgr = TrackingManager()

    # Track 1: Motorcycle
    for f in range(5):
        mgr.update_track(1, "Motorcycle", (100, 150, 180, 260), 0.9, f, f * 0.1)

    # Track 2: Rider (Pedestrian bounding box associated with motorcycle)
    for f in range(5):
        mgr.update_track(2, "Pedestrian", (110, 120, 160, 220), 0.85, f, f * 0.1, is_rider=True, associated_vehicle="Motorcycle")

    # Track 3: Genuine walking pedestrian
    for f in range(5):
        mgr.update_track(3, "Pedestrian", (400, 120, 430, 200), 0.8, f, f * 0.1, is_rider=False)

    unique_veh, counts_by_class, unique_peds = mgr.get_unique_vehicle_metrics()
    assert unique_veh == 1  # Motorcycle
    assert unique_peds == 1  # Only Track 3, Track 2 rider is excluded from pedestrians
    assert counts_by_class.get("Rider") == 1
    assert counts_by_class.get("Pedestrian") == 1
    assert counts_by_class.get("Motorcycle") == 1
