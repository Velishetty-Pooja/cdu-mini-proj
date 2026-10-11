from typing import List, Dict, Optional, Tuple, Any
import numpy as np

from .config import (
    CONGESTION_LOW_THRESHOLD,
    CONGESTION_MODERATE_THRESHOLD,
    SUPPORTED_VEHICLE_CLASSES,
    PEDESTRIAN_CLASSES,
)
from .schemas import (
    BoundingBox,
    CongestionMetrics,
    PedestrianMetrics,
    TrafficEvent,
)
from .tracker import TrackedEntity


class CongestionAnalyzer:
    """
    Interpretable traffic congestion estimation and pedestrian density analysis.
    Uses pixel area occupancy ratio and vehicle count relative to the active roadway.
    """

    @staticmethod
    def calculate_congestion(
        detections: List[BoundingBox],
        img_w: int,
        img_h: int,
        road_roi: Optional[List[float]] = None,
        avg_speed_px_per_sec: Optional[float] = None,
    ) -> CongestionMetrics:
        """
        Calculates road area occupancy ratio:
        Occupancy = (Sum of vehicle bounding box areas inside ROI) / (ROI Area)
        """
        # Determine ROI area
        if road_roi and len(road_roi) == 4:
            roi_w = max(10, int((road_roi[2] - road_roi[0]) * img_w))
            roi_h = max(10, int((road_roi[3] - road_roi[1]) * img_h))
            roi_area = float(roi_w * roi_h)
            rx1 = road_roi[0] * img_w
            ry1 = road_roi[1] * img_h
            rx2 = road_roi[2] * img_w
            ry2 = road_roi[3] * img_h
        else:
            roi_area = float(img_w * img_h)
            rx1, ry1, rx2, ry2 = 0.0, 0.0, float(img_w), float(img_h)

        total_vehicle_box_area = 0.0
        vehicle_count = 0

        for d in detections:
            if d.class_name not in SUPPORTED_VEHICLE_CLASSES:
                continue

            # Check if detection center is within ROI
            cx = (d.x1 + d.x2) / 2.0
            cy = (d.y1 + d.y2) / 2.0

            if rx1 <= cx <= rx2 and ry1 <= cy <= ry2:
                vehicle_count += 1
                bw = max(0.0, d.x2 - d.x1)
                bh = max(0.0, d.y2 - d.y1)
                total_vehicle_box_area += (bw * bh)

        # Occupancy ratio clamped to 0.0 - 1.0
        occupancy_ratio = min(1.0, total_vehicle_box_area / roi_area) if roi_area > 0 else 0.0
        score = round(occupancy_ratio, 3)

        # Congestion level classification
        if occupancy_ratio < CONGESTION_LOW_THRESHOLD:
            level = "Low"
            desc = f"Light traffic flow. Roadway area occupancy is {round(occupancy_ratio * 100, 1)}% with {vehicle_count} active vehicle(s)."
        elif occupancy_ratio < CONGESTION_MODERATE_THRESHOLD:
            level = "Moderate"
            desc = f"Moderate traffic volume. Roadway occupancy is {round(occupancy_ratio * 100, 1)}% with {vehicle_count} active vehicle(s)."
        else:
            level = "High"
            desc = f"Heavy traffic congestion detected. Roadway area occupancy reached {round(occupancy_ratio * 100, 1)}% with {vehicle_count} vehicle(s)."

        method_note = (
            "Occupancy ratio computed as cumulative 2D bounding-box area coverage relative to active road corridor. "
            "Real-world speed in km/h is omitted in adherence to scientific standards due to absence of metric camera calibration."
        )

        return CongestionMetrics(
            level=level,
            score=score,
            vehicle_count=vehicle_count,
            occupancy_ratio=round(occupancy_ratio, 4),
            avg_speed_px_per_sec=round(avg_speed_px_per_sec, 1) if avg_speed_px_per_sec is not None else None,
            description=desc,
            methodology_note=method_note,
        )

    @staticmethod
    def calculate_pedestrian_density(
        detections: List[BoundingBox],
        img_w: int,
        img_h: int,
        unique_pedestrians: Optional[int] = None,
    ) -> PedestrianMetrics:
        """
        Estimates pedestrian density and road exposure.
        """
        pedestrians = [d for d in detections if d.class_name in PEDESTRIAN_CLASSES]
        count = len(pedestrians)

        # Approximate density score based on pedestrian counts
        if count == 0:
            level = "Low"
            score = 0.0
            desc = "No pedestrians detected in the active frame."
        elif count <= 3:
            level = "Low"
            score = 0.2
            desc = f"Low pedestrian activity observed ({count} pedestrian(s))."
        elif count <= 8:
            level = "Moderate"
            score = 0.55
            desc = f"Moderate pedestrian foot traffic ({count} pedestrians observed)."
        else:
            level = "High"
            score = 0.85
            desc = f"High pedestrian density ({count} pedestrians observed in roadway zone)."

        limitations_note = (
            "Pedestrian detection is subject to occlusion, camera height, and lighting conditions. "
            "Identity tracking or facial analysis is strictly non-operational to protect privacy."
        )

        return PedestrianMetrics(
            count=count,
            unique_count=unique_pedestrians,
            density_level=level,
            density_score=score,
            in_crossing_zone_count=count,
            description=desc,
            limitations_note=limitations_note,
        )

    @staticmethod
    def detect_stationary_vehicles(
        active_entities: List[TrackedEntity],
        min_stopped_seconds: float = 3.5,
        max_movement_px: float = 15.0,
    ) -> List[Tuple[TrackedEntity, str]]:
        """
        Detects vehicles that have been stationary in active lanes for longer than threshold duration.
        """
        stopped: List[Tuple[TrackedEntity, str]] = []
        for ent in active_entities:
            if not ent.is_vehicle or ent.stationary_event_emitted:
                continue

            if ent.duration_seconds >= min_stopped_seconds and ent.total_displacement <= max_movement_px:
                ent.stationary_event_emitted = True
                reason = (
                    f"Vehicle #{ent.track_id} ({ent.dominant_class}) has remained stationary for "
                    f"{ent.duration_seconds:.1f}s with minimal movement ({ent.total_displacement:.1f}px), "
                    "indicating a potential breakdown, obstruction, or halted traffic."
                )
                stopped.append((ent, reason))

        return stopped
