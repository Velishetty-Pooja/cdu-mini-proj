import math
import uuid
from typing import Dict, List, Optional, Tuple, Any, Set
import numpy as np

from .config import (
    DEFAULT_MIN_DISPLACEMENT_PX,
    DEFAULT_MIN_OBSERVATION_FRAMES,
    DEFAULT_WRONG_SIDE_COSINE_THRESHOLD,
    PEDESTRIAN_CLASSES,
)
from .schemas import (
    TrafficEvent,
    LaneDefinition,
    CountingLineDefinition,
    CountingLineResult,
)
from .tracker import TrackedEntity


def get_direction_vector(direction_name: str) -> Tuple[float, float]:
    """Returns normalized unit vector (dx, dy) for cardinal, diagonal directions or degree angles."""
    direction = str(direction_name).lower().strip().replace(" ", "_").replace("-", "_")
    
    # Diagonal directions (sqrt(0.5) ~ 0.7071)
    if direction in ["down_right", "southeast", "se"]:
        return (0.7071, 0.7071)
    elif direction in ["down_left", "southwest", "sw"]:
        return (-0.7071, 0.7071)
    elif direction in ["up_right", "northeast", "ne"]:
        return (0.7071, -0.7071)
    elif direction in ["up_left", "northwest", "nw"]:
        return (-0.7071, -0.7071)
    # Cardinal directions
    elif direction in ["down", "south", "forward", "s"]:
        return (0.0, 1.0)
    elif direction in ["up", "north", "backward", "reverse", "n"]:
        return (0.0, -1.0)
    elif direction in ["left", "west", "w"]:
        return (-1.0, 0.0)
    elif direction in ["right", "east", "e"]:
        return (1.0, 0.0)

    # Check if specified as numeric angle in degrees (e.g. "90", "135 deg")
    try:
        clean_deg = direction.replace("deg", "").replace("°", "").strip()
        deg = float(clean_deg)
        rad = math.radians(deg)
        return (round(math.cos(rad), 4), round(math.sin(rad), 4))
    except (ValueError, TypeError):
        pass

    return (0.0, 1.0)  # Default downward flow


def cosine_similarity(v1: Tuple[float, float], v2: Tuple[float, float]) -> float:
    """Computes cosine similarity between two 2D vectors."""
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.hypot(v1[0], v1[1])
    mag2 = math.hypot(v2[0], v2[1])
    if mag1 < 1e-6 or mag2 < 1e-6:
        return 0.0
    return dot / (mag1 * mag2)


def is_point_in_box(
    x: float, y: float, box: List[float], img_w: int, img_h: int
) -> bool:
    """Checks if point (x, y) in pixel coords is inside normalized [x1, y1, x2, y2] box."""
    if len(box) != 4:
        return False
    bx1 = box[0] * img_w
    by1 = box[1] * img_h
    bx2 = box[2] * img_w
    by2 = box[3] * img_h
    return bx1 <= x <= bx2 and by1 <= y <= by2


def line_segments_intersect(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    p3: Tuple[float, float],
    p4: Tuple[float, float],
) -> Tuple[bool, float]:
    """
    Checks if line segment p1->p2 intersects p3->p4 using cross product orientations.
    Returns (intersects: bool, cross_product_sign: float).
    """
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    intersect = (ccw(p1, p3, p4) != ccw(p2, p3, p4)) and (ccw(p1, p2, p3) != ccw(p1, p2, p4))
    if not intersect:
        return False, 0.0

    # Determine orientation/direction of crossing
    line_dx = p4[0] - p3[0]
    line_dy = p4[1] - p3[1]
    move_dx = p2[0] - p1[0]
    move_dy = p2[1] - p1[1]
    cross = line_dx * move_dy - line_dy * move_dx
    return True, cross


class TrafficRulesEngine:
    """
    Evidence-based evaluation for:
    - Wrong-side / opposite direction driving
    - Lane-specific permitted directions and vehicle restrictions
    - Restricted zone entry
    - Virtual counting line crossings
    """

    def __init__(
        self,
        expected_direction: Optional[str] = "down",
        road_roi: Optional[List[float]] = None,
        lanes: Optional[List[LaneDefinition]] = None,
        counting_lines: Optional[List[CountingLineDefinition]] = None,
        restricted_zones: Optional[List[List[float]]] = None,
        min_displacement_px: float = DEFAULT_MIN_DISPLACEMENT_PX,
        min_observation_frames: int = DEFAULT_MIN_OBSERVATION_FRAMES,
        cosine_threshold: float = DEFAULT_WRONG_SIDE_COSINE_THRESHOLD,
    ):
        self.expected_direction = expected_direction
        self.road_roi = road_roi
        self.lanes = lanes or []
        self.counting_lines = counting_lines or []
        self.restricted_zones = restricted_zones or []
        self.min_displacement_px = min_displacement_px
        self.min_observation_frames = min_observation_frames
        self.cosine_threshold = cosine_threshold

        # Counting line state: line_id -> {"forward": int, "reverse": int, "total": int}
        self.line_crossing_counts: Dict[str, Dict[str, int]] = {
            getattr(cl, "id", str(i)): {"forward": 0, "reverse": 0, "total": 0}
            for i, cl in enumerate(self.counting_lines)
        }

    def evaluate_wrong_side(
        self,
        entity: TrackedEntity,
        img_w: int,
        img_h: int,
    ) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Evaluates whether a tracked vehicle is travelling against the configured expected direction.
        Returns: (is_wrong_side: bool, reason: str, cosine_sim: float)
        """
        # 1. Reject pedestrians and riders
        if entity.is_pedestrian or entity.dominant_class in PEDESTRIAN_CLASSES or getattr(entity, "is_rider", False):
            return False, "Pedestrians are exempt from vehicular direction rules", None

        # 2. Check if road direction is configured
        if not self.expected_direction and not self.lanes:
            return False, "No road travel direction configured; direction evaluation skipped", None

        # 3. Check minimum observation duration
        if len(entity.history) < self.min_observation_frames:
            return False, f"Insufficient observation frames ({len(entity.history)} < {self.min_observation_frames})", None

        # 4. Check road ROI if configured
        latest_pt = entity.history[-1]
        if self.road_roi:
            if not is_point_in_box(latest_pt.x, latest_pt.y, self.road_roi, img_w, img_h):
                return False, "Vehicle is outside configured Road ROI corridor", None

        # 5. Check displacement to filter out stationary / jittering vehicles
        disp_mag = entity.total_displacement
        if disp_mag < self.min_displacement_px:
            return False, f"Negligible displacement ({disp_mag:.1f}px < {self.min_displacement_px}px threshold); stationary or jitter", None

        # 6. Determine expected direction for vehicle's specific lane or global road
        expected_dir_name = self.expected_direction or "down"
        lane_matched_name = "Global Corridor"

        for lane in self.lanes:
            lbounds = getattr(lane, "bounds", None) or lane.get("bounds")
            ldir = getattr(lane, "permitted_direction", None) or lane.get("permitted_direction")
            lname = getattr(lane, "name", None) or lane.get("name", "Lane")
            if lbounds and is_point_in_box(latest_pt.x, latest_pt.y, lbounds, img_w, img_h):
                expected_dir_name = ldir
                lane_matched_name = lname
                break

        if expected_dir_name == "bidirectional":
            return False, f"Vehicle in bidirectional lane '{lane_matched_name}'", None

        expected_vec = get_direction_vector(expected_dir_name)
        obs_vec = entity.displacement_vector
        sim = cosine_similarity(obs_vec, expected_vec)

        # Smooth directional score using recent sliding window if vehicle has moved significantly recently
        if hasattr(entity, "get_recent_displacement_vector"):
            recent_vec = entity.get_recent_displacement_vector(window=15)
            recent_mag = math.hypot(recent_vec[0], recent_vec[1])
            if recent_mag >= self.min_displacement_px * 0.7:
                recent_sim = cosine_similarity(recent_vec, expected_vec)
                sim = 0.65 * sim + 0.35 * recent_sim

        # 7. Check cosine similarity against configured threshold
        if sim < self.cosine_threshold:
            reason = (
                f"Trajectory in '{lane_matched_name}' is directed against configured flow "
                f"({expected_dir_name.upper()}). Net vector ({obs_vec[0]:.1f}, {obs_vec[1]:.1f}) "
                f"yields directional alignment score of {sim:.2f} (threshold: {self.cosine_threshold:.2f})."
            )
            return True, reason, sim

        return False, f"Trajectory conforms to flow ({sim:.2f} >= {self.cosine_threshold:.2f})", sim

    def evaluate_lane_violations(
        self,
        entity: TrackedEntity,
        img_w: int,
        img_h: int,
    ) -> List[Tuple[str, str]]:
        """
        Evaluates lane-specific restrictions (e.g. vehicle class restrictions, restricted zones).
        Returns list of (violation_type, reason).
        """
        violations: List[Tuple[str, str]] = []
        if len(entity.history) == 0:
            return violations

        latest_pt = entity.history[-1]

        # Check restricted zones
        for i, zone in enumerate(self.restricted_zones):
            if is_point_in_box(latest_pt.x, latest_pt.y, zone, img_w, img_h):
                violations.append((
                    "restricted_entry",
                    f"Vehicle #{entity.track_id} ({entity.dominant_class}) entered restricted road zone #{i+1}."
                ))

        # Check lane vehicle class restrictions
        for lane in self.lanes:
            lbounds = getattr(lane, "bounds", None) or lane.get("bounds")
            lclasses = getattr(lane, "permitted_classes", None) or lane.get("permitted_classes")
            lname = getattr(lane, "name", None) or lane.get("name", "Lane")

            if lbounds and lclasses and is_point_in_box(latest_pt.x, latest_pt.y, lbounds, img_w, img_h):
                if entity.dominant_class not in lclasses:
                    violations.append((
                        "lane_violation",
                        f"Vehicle #{entity.track_id} ({entity.dominant_class}) occupied dedicated '{lname}' "
                        f"reserved exclusively for: {', '.join(lclasses)}."
                    ))

        return violations

    def check_counting_lines(
        self,
        entity: TrackedEntity,
        img_w: int,
        img_h: int,
    ) -> List[Tuple[str, str, str]]:
        """
        Checks if entity's movement in the latest frame crossed any virtual counting lines.
        Returns list of (line_id, line_name, crossing_direction).
        """
        if len(entity.history) < 2:
            return []

        p_prev = (entity.history[-2].x, entity.history[-2].y)
        p_curr = (entity.history[-1].x, entity.history[-1].y)

        crossings: List[Tuple[str, str, str]] = []

        for cl in self.counting_lines:
            lid = getattr(cl, "id", None) or cl.get("id")
            lname = getattr(cl, "name", None) or cl.get("name", "Line")
            coords = getattr(cl, "coords", None) or cl.get("coords")

            if lid in entity.crossed_lines or not coords or len(coords) != 4:
                continue

            l_p1 = (coords[0] * img_w, coords[1] * img_h)
            l_p2 = (coords[2] * img_w, coords[3] * img_h)

            intersect, cross_sign = line_segments_intersect(p_prev, p_curr, l_p1, l_p2)
            if intersect:
                direction = "forward" if cross_sign > 0 else "reverse"
                entity.crossed_lines.add(lid)
                if lid not in self.line_crossing_counts:
                    self.line_crossing_counts[lid] = {"forward": 0, "reverse": 0, "total": 0}

                self.line_crossing_counts[lid][direction] += 1
                self.line_crossing_counts[lid]["total"] += 1
                crossings.append((lid, lname, direction))

        return crossings

    def get_counting_line_results(self) -> List[CountingLineResult]:
        results: List[CountingLineResult] = []
        for cl in self.counting_lines:
            lid = getattr(cl, "id", None) or cl.get("id")
            lname = getattr(cl, "name", None) or cl.get("name", "Line")
            counts = self.line_crossing_counts.get(lid, {"forward": 0, "reverse": 0, "total": 0})
            results.append(
                CountingLineResult(
                    line_id=lid,
                    line_name=lname,
                    forward_count=counts["forward"],
                    reverse_count=counts["reverse"],
                    total_crossings=counts["total"],
                )
            )
        return results
