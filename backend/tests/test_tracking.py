from app.tracker import TrackingManager


def test_track_history_and_displacement():
    mgr = TrackingManager()

    # Track moving down from y=100 to y=250 over 6 frames
    for i in range(6):
        mgr.update_track(
            track_id=10,
            class_name="Car",
            bbox=(100.0, 100.0 + i * 30, 150.0, 150.0 + i * 30),
            confidence=0.9,
            frame_idx=i,
            timestamp_seconds=i * 0.2,
        )

    entity = mgr.get_entity(10)
    assert entity is not None
    assert len(entity.history) == 6
    assert entity.dominant_class == "Car"
    assert entity.is_vehicle is True
    assert entity.is_pedestrian is False

    # First point bottom center: (125.0, 150.0)
    # Last point bottom center: (125.0, 300.0)
    # Total displacement = 150.0
    assert round(entity.total_displacement, 1) == 150.0

    # Net vector: dx=0.0, dy=150.0
    dx, dy = entity.displacement_vector
    assert round(dx, 1) == 0.0
    assert round(dy, 1) == 150.0

    # Duration: 5 * 0.2 = 1.0s
    assert round(entity.duration_seconds, 1) == 1.0
    # Speed: 150 px / 1.0s = 150 px/s
    assert round(entity.avg_speed_px_per_sec, 1) == 150.0


def test_track_class_majority_voting():
    mgr = TrackingManager()
    # 4 detections as Motorcycle, 1 noisy detection as Bicycle
    mgr.update_track(5, "Motorcycle", (10, 10, 30, 30), 0.8, 0, 0.0)
    mgr.update_track(5, "Motorcycle", (10, 15, 30, 35), 0.82, 1, 0.1)
    mgr.update_track(5, "Bicycle", (10, 20, 30, 40), 0.45, 2, 0.2)
    mgr.update_track(5, "Motorcycle", (10, 25, 30, 45), 0.85, 3, 0.3)
    mgr.update_track(5, "Motorcycle", (10, 30, 30, 50), 0.89, 4, 0.4)

    entity = mgr.get_entity(5)
    assert entity is not None
    assert entity.dominant_class == "Motorcycle"
