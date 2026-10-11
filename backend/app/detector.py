import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Set
from ultralytics import YOLO

from .config import (
    YOLO_MODEL_PATH,
    DEVICE,
    COCO_CLASS_MAP,
    SUPPORTED_VEHICLE_CLASSES,
    PEDESTRIAN_CLASSES,
    DEFAULT_CONFIDENCE,
    DEFAULT_IOU,
)
from .schemas import BoundingBox, ClassCount


# Professional high-contrast BGR colors for visualization
CLASS_COLORS: Dict[str, Tuple[int, int, int]] = {
    "Car": (255, 160, 40),          # Bright Azure / Blue
    "Motorcycle": (30, 200, 255),    # Golden Amber
    "Bus": (210, 50, 180),           # Violet / Fuchsia
    "Truck": (20, 110, 245),         # Deep Flame Orange
    "Bicycle": (230, 220, 30),       # Bright Cyan
    "Pedestrian": (60, 220, 90),     # Emerald Green
    "Rider": (245, 180, 50),         # Warm Amber Gold
    "Auto-rickshaw": (0, 165, 255),  # Saffron Yellow
    "Violation": (40, 40, 235),      # Alert Red
}
DEFAULT_BOX_COLOR: Tuple[int, int, int] = (200, 200, 200)


class DetectorService:
    """
    Real object detection engine using Ultralytics YOLO with strict class mapping,
    bounding box validation, and metric aggregation.
    """

    def __init__(self, model_path: str = YOLO_MODEL_PATH, device: str = DEVICE):
        self.model_path = model_path
        self.device = device
        self.model: Optional[YOLO] = None
        self._load_model()

    def _load_model(self):
        """Loads YOLO model weights. Raises descriptive error if weights are missing or corrupt."""
        model_file = Path(self.model_path)
        if not model_file.exists() and not self.model_path.endswith(".pt"):
            raise FileNotFoundError(
                f"YOLO model weights file not found at '{self.model_path}'. "
                "Ensure yolov8n.pt exists or provide a valid model path."
            )

        try:
            self.model = YOLO(self.model_path)
            self.model.to(self.device)
            # Verify supported classes from model's internal names
            self.model_names = self.model.names
            self.traffic_class_ids = [
                cid for cid, cname in self.model_names.items()
                if cid in COCO_CLASS_MAP or any(
                    k in cname.lower()
                    for k in ["car", "bus", "truck", "motorcycle", "bike", "bicycle", "person", "pedestrian", "rickshaw"]
                )
            ]
        except Exception as e:
            raise RuntimeError(
                f"Failed to load YOLO model weights from '{self.model_path}': {str(e)}. "
                "Verify PyTorch and Ultralytics installations."
            )

    def map_class_id(self, class_id: int, raw_name: str) -> Optional[str]:
        """
        Maps model internal class ID to application standardized traffic class name.
        Does not pretend unsupported classes were detected.
        """
        if class_id in COCO_CLASS_MAP:
            return COCO_CLASS_MAP[class_id]

        # Name-based fallback for custom-trained models (e.g. Indian driving dataset)
        lower = raw_name.lower()
        if "rickshaw" in lower or "auto" in lower:
            return "Auto-rickshaw"
        if "car" in lower:
            return "Car"
        if "motorcycle" in lower or "bike" in lower or "scooter" in lower:
            return "Motorcycle"
        if "bus" in lower:
            return "Bus"
        if "truck" in lower:
            return "Truck"
        if "bicycle" in lower or "cycle" in lower:
            return "Bicycle"
        if "person" in lower or "pedestrian" in lower:
            return "Pedestrian"

        return None

    def detect_image(
        self,
        image: np.ndarray,
        confidence_threshold: float = DEFAULT_CONFIDENCE,
        iou_threshold: float = DEFAULT_IOU,
    ) -> List[BoundingBox]:
        """
        Performs inference on a single image frame (BGR format numpy array).
        Returns validated, coordinate-clipped BoundingBox objects.
        """
        if self.model is None:
            raise RuntimeError("Detector model is not initialized.")

        img_h, img_w = image.shape[:2]
        if img_h == 0 or img_w == 0:
            return []

        # Run inference
        results = self.model(
            image,
            conf=confidence_threshold,
            iou=iou_threshold,
            classes=self.traffic_class_ids,
            verbose=False,
            device=self.device,
        )

        detections: List[BoundingBox] = []
        if not results or len(results) == 0:
            return detections

        r = results[0]
        boxes = r.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        xyxy = boxes.xyxy.cpu().numpy()
        confs = boxes.conf.cpu().numpy()
        classes = boxes.cls.cpu().numpy().astype(int)

        for i in range(len(xyxy)):
            cid = int(classes[i])
            raw_name = self.model_names.get(cid, "unknown")
            mapped_label = self.map_class_id(cid, raw_name)
            if not mapped_label:
                continue

            conf = float(confs[i])
            x1, y1, x2, y2 = xyxy[i]

            # Strictly clip bounding box to valid image dimensions
            x1 = max(0.0, min(float(x1), float(img_w - 1)))
            y1 = max(0.0, min(float(y1), float(img_h - 1)))
            x2 = max(x1 + 1.0, min(float(x2), float(img_w)))
            y2 = max(y1 + 1.0, min(float(y2), float(img_h)))

            detections.append(
                BoundingBox(
                    x1=round(x1, 1),
                    y1=round(y1, 1),
                    x2=round(x2, 1),
                    y2=round(y2, 1),
                    confidence=round(conf, 4),
                    class_name=mapped_label,
                    model_class_id=cid,
                )
            )

        self.associate_riders(detections)
        return detections

    @staticmethod
    def associate_riders(detections: List[BoundingBox]) -> List[BoundingBox]:
        """
        Associates persons riding two-wheelers (Motorcycle, Bicycle) so they are
        correctly labeled as riders rather than counted as independent pedestrians.
        Updates is_rider and associated_vehicle in-place.
        """
        two_wheelers = [d for d in detections if d.class_name in ("Motorcycle", "Bicycle")]
        persons = [d for d in detections if d.class_name in PEDESTRIAN_CLASSES or d.class_name == "Person"]

        for p in persons:
            p_area = max(1.0, (p.x2 - p.x1) * (p.y2 - p.y1))
            p_cx = (p.x1 + p.x2) / 2.0
            p_bottom_y = p.y2
            p_cy = (p.y1 + p.y2) / 2.0

            best_bike = None
            best_overlap = 0.0

            for v in two_wheelers:
                ix1 = max(p.x1, v.x1)
                iy1 = max(p.y1, v.y1)
                ix2 = min(p.x2, v.x2)
                iy2 = min(p.y2, v.y2)

                inter_w = max(0.0, ix2 - ix1)
                inter_h = max(0.0, iy2 - iy1)
                inter_area = inter_w * inter_h
                iop = inter_area / p_area

                v_w = v.x2 - v.x1
                v_h = v.y2 - v.y1

                # Spatial heuristics:
                # 1. Person center x is within the horizontal range of the vehicle (with margin)
                h_match = (v.x1 - 0.25 * v_w <= p_cx <= v.x2 + 0.25 * v_w)
                # 2. Person sits atop the two-wheeler: bottom of person is inside the vehicle's vertical span
                # or person center y is inside or slightly above
                v_match = (v.y1 - 0.15 * v_h <= p_bottom_y <= v.y2 + 0.15 * v_h) or (v.y1 <= p_cy <= v.y2)

                # Sufficient overlap or containment
                if (iop >= 0.18) or (h_match and v_match and (iop >= 0.08 or (v.y1 <= p_bottom_y <= v.y2))):
                    if iop > best_overlap:
                        best_overlap = iop
                        best_bike = v

            if best_bike is not None:
                p.is_rider = True
                p.associated_vehicle = best_bike.class_name

        return detections

    @staticmethod
    def aggregate_class_counts(detections: List[BoundingBox]) -> Tuple[List[ClassCount], int, int]:
        """
        Aggregates class counts directly from real detections.
        Distinguishes independent pedestrians from vehicle riders.
        Returns:
            - List of ClassCount objects with exact percentage calculation
            - Total vehicle count (excluding pedestrians)
            - Total pedestrian count (excluding riders)
        """
        raw_counts: Dict[str, int] = {}
        total_vehicles = 0
        total_pedestrians = 0

        for d in detections:
            if d.is_rider:
                raw_counts["Rider"] = raw_counts.get("Rider", 0) + 1
            elif d.class_name in PEDESTRIAN_CLASSES:
                total_pedestrians += 1
                raw_counts["Pedestrian"] = raw_counts.get("Pedestrian", 0) + 1
            elif d.class_name in SUPPORTED_VEHICLE_CLASSES:
                total_vehicles += 1
                raw_counts[d.class_name] = raw_counts.get(d.class_name, 0) + 1
            else:
                raw_counts[d.class_name] = raw_counts.get(d.class_name, 0) + 1

        total_all = sum(raw_counts.values())
        class_counts: List[ClassCount] = []

        # Sort with vehicles first, then riders, then pedestrians
        sorted_classes = sorted(
            raw_counts.keys(),
            key=lambda c: (c in PEDESTRIAN_CLASSES or c == "Rider", -raw_counts[c])
        )

        for cname in sorted_classes:
            cnt = raw_counts[cname]
            pct = round((cnt / total_all) * 100.0, 1) if total_all > 0 else 0.0
            class_counts.append(ClassCount(class_name=cname, count=cnt, percentage=pct))

        return class_counts, total_vehicles, total_pedestrians

    @staticmethod
    def annotate_image(
        image: np.ndarray,
        detections: List[BoundingBox],
        road_roi: Optional[List[float]] = None,
        lanes: Optional[List[Any]] = None,
        counting_lines: Optional[List[Any]] = None,
        highlight_violations: Optional[Set[int]] = None,
    ) -> np.ndarray:
        """
        Draws professional bounding boxes, labels, confidence scores, and ROI overlays.
        """
        canvas = image.copy()
        img_h, img_w = canvas.shape[:2]

        # 1. Draw Road ROI if configured
        if road_roi and len(road_roi) == 4:
            rx1, ry1, rx2, ry2 = [
                int(road_roi[0] * img_w),
                int(road_roi[1] * img_h),
                int(road_roi[2] * img_w),
                int(road_roi[3] * img_h),
            ]
            overlay = canvas.copy()
            cv2.rectangle(overlay, (rx1, ry1), (rx2, ry2), (60, 180, 240), 2)
            cv2.putText(
                canvas,
                "ROI: Active Road Corridor",
                (rx1 + 10, max(25, ry1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (60, 180, 240),
                1,
                cv2.LINE_AA,
            )

        # 2. Draw Counting Lines if configured
        if counting_lines:
            for cl in counting_lines:
                coords = getattr(cl, "coords", None) or cl.get("coords")
                name = getattr(cl, "name", None) or cl.get("name", "Counting Line")
                if coords and len(coords) == 4:
                    lx1, ly1, lx2, ly2 = (
                        int(coords[0] * img_w),
                        int(coords[1] * img_h),
                        int(coords[2] * img_w),
                        int(coords[3] * img_h),
                    )
                    cv2.line(canvas, (lx1, ly1), (lx2, ly2), (0, 235, 255), 2, cv2.LINE_AA)
                    cv2.putText(
                        canvas,
                        f"Line: {name}",
                        (min(lx1, lx2) + 10, min(ly1, ly2) - 8),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 235, 255),
                        1,
                        cv2.LINE_AA,
                    )

        # 3. Draw Detections
        for d in detections:
            is_violating = highlight_violations and (d.track_id in highlight_violations)
            if is_violating:
                color = CLASS_COLORS["Violation"]
            elif d.is_rider:
                color = CLASS_COLORS.get("Rider", (245, 180, 50))
            else:
                color = CLASS_COLORS.get(d.class_name, DEFAULT_BOX_COLOR)

            x1, y1, x2, y2 = int(d.x1), int(d.y1), int(d.x2), int(d.y2)
            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

            # Build label text
            if d.is_rider:
                veh_info = f" ({d.associated_vehicle})" if d.associated_vehicle else ""
                if d.track_id is not None:
                    label = f"#{d.track_id} Rider{veh_info} {int(d.confidence * 100)}%"
                else:
                    label = f"Rider{veh_info} {int(d.confidence * 100)}%"
            elif d.track_id is not None:
                label = f"#{d.track_id} {d.class_name} {int(d.confidence * 100)}%"
            else:
                label = f"{d.class_name} {int(d.confidence * 100)}%"

            (lw, lh), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            label_y1 = max(0, y1 - lh - 6)
            label_y2 = y1

            # Filled tag background
            cv2.rectangle(canvas, (x1, label_y1), (x1 + lw + 8, label_y2), color, -1)
            cv2.putText(
                canvas,
                label,
                (x1 + 4, label_y2 - 3),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (10, 10, 10),
                1,
                cv2.LINE_AA,
            )

        return canvas
