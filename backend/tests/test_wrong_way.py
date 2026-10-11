from app.tracker import TrackingManager
from app.traffic_rules import TrafficRulesEngine
from app.schemas import LaneDefinition


def test_movement_in_expected_direction():
    """Movement aligned with expected direction should NOT be flagged as wrong-side."""
    mgr = TrackingManager()
    rules = TrafficRulesEngine(expected_direction="down", min_displacement_px=20.0, min_observation_frames=4)

    # Moving down from y=50 to y=150
    for f in range(6):
        mgr.update_track(1, "Car", (100, 50 + f * 20, 150, 100 + f * 20), 0.9, f, f * 0.1)

    ent = mgr.get_entity(1)
    is_wrong, reason, sim = rules.evaluate_wrong_side(ent, 640, 480)
    assert is_wrong is False
    assert sim is not None and sim > 0.8


def test_movement_against_configured_direction():
    """Movement opposite to expected direction should be flagged as wrong-side."""
    mgr = TrackingManager()
    rules = TrafficRulesEngine(expected_direction="down", min_displacement_px=20.0, min_observation_frames=4)

    # Moving UP (against "down" flow) from y=300 down to y=200
    for f in range(6):
        mgr.update_track(2, "Motorcycle", (100, 300 - f * 20, 130, 340 - f * 20), 0.88, f, f * 0.1)

    ent = mgr.get_entity(2)
    is_wrong, reason, sim = rules.evaluate_wrong_side(ent, 640, 480)
    assert is_wrong is True
    assert "against configured flow" in reason
    assert sim is not None and sim < -0.8


def test_negligible_movement_not_flagged():
    """Stationary or jittering vehicle should NOT be flagged as wrong-side."""
    mgr = TrackingManager()
    rules = TrafficRulesEngine(expected_direction="down", min_displacement_px=30.0, min_observation_frames=4)

    # Jittering in place by 2 pixels
    for f in range(6):
        jitter = 1 if f % 2 == 0 else -1
        mgr.update_track(3, "Car", (100 + jitter, 100, 150 + jitter, 150), 0.9, f, f * 0.1)

    ent = mgr.get_entity(3)
    is_wrong, reason, sim = rules.evaluate_wrong_side(ent, 640, 480)
    assert is_wrong is False
    assert "Negligible displacement" in reason


def test_noisy_trajectories_with_overall_correct_flow():
    """Trajectories with minor lateral noise but overall correct flow should not be flagged."""
    mgr = TrackingManager()
    rules = TrafficRulesEngine(expected_direction="down", min_displacement_px=25.0, min_observation_frames=4)

    # Moving down by 100px with small lateral wobble (+/- 5px)
    for f in range(6):
        dx = 5 if f % 2 == 0 else -5
        mgr.update_track(4, "Car", (100 + dx, 50 + f * 20, 150 + dx, 100 + f * 20), 0.9, f, f * 0.1)

    ent = mgr.get_entity(4)
    is_wrong, reason, sim = rules.evaluate_wrong_side(ent, 640, 480)
    assert is_wrong is False


def test_insufficient_observation_duration():
    """Vehicle observed for fewer frames than threshold should not be flagged."""
    mgr = TrackingManager()
    rules = TrafficRulesEngine(expected_direction="down", min_displacement_px=20.0, min_observation_frames=5)

    # Moving up for only 2 frames
    mgr.update_track(5, "Car", (100, 200, 150, 250), 0.9, 0, 0.0)
    mgr.update_track(5, "Car", (100, 160, 150, 210), 0.9, 1, 0.1)

    ent = mgr.get_entity(5)
    is_wrong, reason, sim = rules.evaluate_wrong_side(ent, 640, 480)
    assert is_wrong is False
    assert "Insufficient observation frames" in reason


def test_vehicles_in_separate_configured_lanes():
    """Dual carriageway: Left lane permits 'down', Right lane permits 'up'."""
    mgr = TrackingManager()
    lane_left = LaneDefinition(id="l1", name="Left Carriageway", bounds=[0.0, 0.0, 0.5, 1.0], permitted_direction="down")
    lane_right = LaneDefinition(id="l2", name="Right Carriageway", bounds=[0.5, 0.0, 1.0, 1.0], permitted_direction="up")

    rules = TrafficRulesEngine(
        expected_direction="down",
        lanes=[lane_left, lane_right],
        min_displacement_px=20.0,
        min_observation_frames=4,
    )

    # Vehicle in Right Carriageway (x=400 in 640px = 62.5% -> lane_right) moving UP -> NORMAL for that lane!
    for f in range(6):
        mgr.update_track(6, "Car", (380, 300 - f * 20, 430, 350 - f * 20), 0.9, f, f * 0.1)

    ent6 = mgr.get_entity(6)
    is_wrong6, reason6, sim6 = rules.evaluate_wrong_side(ent6, 640, 480)
    assert is_wrong6 is False, f"Expected normal in right lane, but got: {reason6}"

    # Vehicle in Left Carriageway (x=100 -> lane_left) moving UP -> WRONG SIDE for left lane!
    for f in range(6):
        mgr.update_track(7, "Car", (100, 300 - f * 20, 150, 350 - f * 20), 0.9, f, f * 0.1)

    ent7 = mgr.get_entity(7)
    is_wrong7, reason7, sim7 = rules.evaluate_wrong_side(ent7, 640, 480)
    assert is_wrong7 is True
    assert "against configured flow" in reason7


def test_missing_direction_configuration():
    """When no direction is configured, evaluation reports skipped status rather than false violations."""
    mgr = TrackingManager()
    rules = TrafficRulesEngine(expected_direction=None, lanes=[])

    for f in range(6):
        mgr.update_track(8, "Car", (100, 200 + f * 20, 150, 250 + f * 20), 0.9, f, f * 0.1)

    ent = mgr.get_entity(8)
    is_wrong, reason, sim = rules.evaluate_wrong_side(ent, 640, 480)
    assert is_wrong is False
    assert "No road travel direction configured" in reason
