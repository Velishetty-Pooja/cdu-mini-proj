from app.tracker import TrackingManager
from app.traffic_rules import TrafficRulesEngine
from app.schemas import LaneDefinition, BoundingBox
from app.congestion import CongestionAnalyzer


def test_dedicated_bus_lane_violation():
    """A Truck occupying a dedicated Bus-only lane should be flagged as a lane violation."""
    bus_lane = LaneDefinition(
        id="bus_lane_1",
        name="Dedicated BRTS Corridor",
        bounds=[0.0, 0.0, 0.3, 1.0],  # Left 30% of roadway
        permitted_direction="down",
        permitted_classes=["Bus"],
    )
    rules = TrafficRulesEngine(lanes=[bus_lane])
    mgr = TrackingManager()

    # Track 1: Bus in Bus lane -> OK
    mgr.update_track(1, "Bus", (50, 100, 120, 160), 0.9, 0, 0.0)
    ent_bus = mgr.get_entity(1)
    viols_bus = rules.evaluate_lane_violations(ent_bus, 640, 480)
    assert len(viols_bus) == 0

    # Track 2: Truck in Bus lane -> VIOLATION
    mgr.update_track(2, "Truck", (50, 100, 120, 160), 0.88, 0, 0.0)
    ent_truck = mgr.get_entity(2)
    viols_truck = rules.evaluate_lane_violations(ent_truck, 640, 480)
    assert len(viols_truck) == 1
    assert viols_truck[0][0] == "lane_violation"
    assert "reserved exclusively" in viols_truck[0][1]


def test_restricted_zone_entry():
    """A vehicle entering a configured restricted zone should be flagged."""
    restricted_box = [0.4, 0.4, 0.6, 0.6]  # Center zone
    rules = TrafficRulesEngine(restricted_zones=[restricted_box])
    mgr = TrackingManager()

    # Vehicle at (x=320, y=240 in 640x480) is at (0.5, 0.5) inside restricted zone
    mgr.update_track(3, "Car", (300, 200, 340, 240), 0.9, 0, 0.0)
    ent = mgr.get_entity(3)
    viols = rules.evaluate_lane_violations(ent, 640, 480)
    assert len(viols) == 1
    assert viols[0][0] == "restricted_entry"


def test_congestion_thresholds():
    """Tests Low, Moderate, and High congestion classifications based on occupancy."""
    w, h = 640, 480
    roi = [0.0, 0.0, 1.0, 1.0]

    # 1 vehicle covering tiny area -> Low
    small_det = [BoundingBox(x1=50, y1=50, x2=100, y2=100, confidence=0.9, class_name="Car", model_class_id=2)]
    cong_low = CongestionAnalyzer.calculate_congestion(small_det, w, h, road_roi=roi)
    assert cong_low.level == "Low"

    # Dense vehicles covering > 45% -> High
    # 640*480 = 307,200. Each 200x200 box is 40,000. 4 boxes = 160,000 (> 50%)
    high_dets = [
        BoundingBox(x1=0, y1=0, x2=200, y2=200, confidence=0.9, class_name="Bus", model_class_id=5),
        BoundingBox(x1=210, y1=0, x2=410, y2=200, confidence=0.9, class_name="Truck", model_class_id=7),
        BoundingBox(x1=0, y1=210, x2=200, y2=410, confidence=0.9, class_name="Bus", model_class_id=5),
        BoundingBox(x1=210, y1=210, x2=410, y2=410, confidence=0.9, class_name="Truck", model_class_id=7),
    ]
    cong_high = CongestionAnalyzer.calculate_congestion(high_dets, w, h, road_roi=roi)
    assert cong_high.level == "High"
