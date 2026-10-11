import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
import numpy as np

from .config import SUPPORTED_VEHICLE_CLASSES, PEDESTRIAN_CLASSES
from .schemas import BoundingBox


@dataclass
class TrackPoint:
    frame_idx: int
    timestamp_seconds: float
    x: float  # bottom center x
    y: float  # bottom center y
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    confidence: float


@dataclass
class TrackedEntity:
    track_id: int
    class_observations: Counter = field(default_factory=Counter)
    history: List[TrackPoint] = field(default_factory=list)
    crossed_lines: Set[str] = field(default_factory=set)
    is_rider: bool = False
    associated_vehicle: Optional[str] = None
    wrong_side_event_emitted: bool = False
    lane_violation_emitted: bool = False
    stationary_event_emitted: bool = False

    @property
    def dominant_class(self) -> str:
        if not self.class_observations:
            return "Unknown"
        return self.class_observations.most_common(1)[0][0]

    @property
    def is_vehicle(self) -> bool:
        return self.dominant_class in SUPPORTED_VEHICLE_CLASSES

    @property
    def is_pedestrian(self) -> bool:
        return (self.dominant_class in PEDESTRIAN_CLASSES or self.dominant_class == "Person") and not self.is_rider

    @property
    def total_displacement(self) -> float:
        """Euclidean distance between first observed position and latest observed position."""
        if len(self.history) < 2:
            return 0.0
        p_start = self.history[0]
        p_end = self.history[-1]
        return math.hypot(p_end.x - p_start.x, p_end.y - p_start.y)

    @property
    def displacement_vector(self) -> Tuple[float, float]:
        """Net displacement vector (dx, dy) from first to last point."""
        if len(self.history) < 2:
            return (0.0, 0.0)
        return (self.history[-1].x - self.history[0].x, self.history[-1].y - self.history[0].y)

    def get_recent_displacement_vector(self, window: int = 15) -> Tuple[float, float]:
        """Calculates displacement vector over a recent sliding window for smoothed trajectory assessment."""
        if len(self.history) < 2:
            return (0.0, 0.0)
        idx = max(0, len(self.history) - window)
        p_start = self.history[idx]
        p_end = self.history[-1]
        return (p_end.x - p_start.x, p_end.y - p_start.y)

    @property
    def duration_seconds(self) -> float:
        if len(self.history) < 2:
            return 0.0
        return max(0.0, self.history[-1].timestamp_seconds - self.history[0].timestamp_seconds)

    @property
    def avg_speed_px_per_sec(self) -> float:
        dur = self.duration_seconds
        if dur <= 0.01:
            return 0.0
        return self.total_displacement / dur


class TrackingManager:
    """
    Manages persistent track states, trajectory analysis, and metric aggregations.
    """

    def __init__(self):
        self.tracks: Dict[int, TrackedEntity] = {}

    def update_track(
        self,
        track_id: int,
        class_name: str,
        bbox: Tuple[float, float, float, float],
        confidence: float,
        frame_idx: int,
        timestamp_seconds: float,
        is_rider: bool = False,
        associated_vehicle: Optional[str] = None,
    ) -> TrackedEntity:
        """Adds or updates an active track with bottom-center coordinate anchoring."""
        x1, y1, x2, y2 = bbox
        bottom_center_x = (x1 + x2) / 2.0
        bottom_center_y = y2

        if track_id not in self.tracks:
            self.tracks[track_id] = TrackedEntity(track_id=track_id)

        entity = self.tracks[track_id]
        entity.class_observations[class_name] += 1
        if is_rider:
            entity.is_rider = True
            if associated_vehicle:
                entity.associated_vehicle = associated_vehicle

        entity.history.append(
            TrackPoint(
                frame_idx=frame_idx,
                timestamp_seconds=timestamp_seconds,
                x=bottom_center_x,
                y=bottom_center_y,
                bbox=bbox,
                confidence=confidence,
            )
        )
        return entity

    def get_entity(self, track_id: int) -> Optional[TrackedEntity]:
        return self.tracks.get(track_id)

    def get_unique_vehicle_metrics(self) -> Tuple[int, Dict[str, int], int]:
        """
        Calculates:
        1. Total unique vehicles observed across entire video
        2. Unique vehicles by class (using dominant class per track ID)
        3. Total unique pedestrians (excluding two-wheeler riders)
        """
        counts_by_class: Dict[str, int] = {}
        unique_vehicles = 0
        unique_pedestrians = 0

        for track_id, entity in self.tracks.items():
            # Require minimum 2 observations to reject fleeting false-positive detections
            if len(entity.history) < 2:
                continue

            dom_class = "Rider" if entity.is_rider else entity.dominant_class
            counts_by_class[dom_class] = counts_by_class.get(dom_class, 0) + 1

            if entity.is_vehicle:
                unique_vehicles += 1
            elif entity.is_pedestrian:
                unique_pedestrians += 1

        return unique_vehicles, counts_by_class, unique_pedestrians
