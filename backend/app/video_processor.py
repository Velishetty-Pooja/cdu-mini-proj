import cv2
import numpy as np
import time
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple, Set

from .config import (
    PROCESSED_DIR,
    EVIDENCE_DIR,
    DEFAULT_CONFIDENCE,
    DEFAULT_SAMPLE_STRIDE,
    SUPPORTED_VEHICLE_CLASSES,
    PEDESTRIAN_CLASSES,
)
from .schemas import (
    BoundingBox,
    ClassCount,
    CongestionMetrics,
    PedestrianMetrics,
    TrafficEvent,
    VehicleSummary,
    AnalysisConfig,
    CountingLineResult,
)
from .detector import DetectorService, CLASS_COLORS
from .tracker import TrackingManager, TrackedEntity
from .traffic_rules import TrafficRulesEngine
from .congestion import CongestionAnalyzer


class VideoProcessor:
    """
    Asynchronous, frame-by-frame video processing pipeline with multi-object tracking,
    evidence-based direction analysis, virtual counting lines, and congestion estimation.
    """

    def __init__(self, detector: DetectorService):
        self.detector = detector

    @staticmethod
    def validate_video(video_path: Path) -> Tuple[int, int, float, int, float]:
        """
        Validates video file using OpenCV.
        Returns (width, height, fps, total_frames, duration_seconds).
        Raises ValueError if video cannot be opened or has no frames.
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file does not exist: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video file. Decoder failed or corrupt file: {video_path.name}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        if width <= 0 or height <= 0 or total_frames <= 0:
            raise ValueError(f"Video stream contains invalid dimensions ({width}x{height}) or 0 frames.")

        if fps <= 0.0 or fps > 240.0:
            fps = 25.0  # Fallback standard fps if header metadata is distorted

        duration_seconds = round(total_frames / fps, 2)
        return width, height, fps, total_frames, duration_seconds

    def process_video(
        self,
        analysis_id: str,
        video_path: Path,
        output_video_path: Path,
        config: AnalysisConfig,
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Processes video frames sequentially, maintaining persistent tracks and generating
        annotated output video and evidence crops.
        """
        start_time = time.time()
        width, height, fps, total_frames, duration_seconds = self.validate_video(video_path)

        cap = cv2.VideoCapture(str(video_path))
        sample_stride = max(1, config.sample_stride)

        # Output video writer (writes raw frames, then transcodes to H.264 via FFmpeg)
        output_video_path.parent.mkdir(parents=True, exist_ok=True)
        raw_output_path = output_video_path.parent / f"raw_{output_video_path.name}"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        effective_fps = max(1.0, fps / sample_stride)
        out_writer = cv2.VideoWriter(str(raw_output_path), fourcc, effective_fps, (width, height))

        # State tracking engines
        tracker_mgr = TrackingManager()
        rules_engine = TrafficRulesEngine(
            expected_direction=config.expected_direction,
            road_roi=config.road_roi,
            lanes=config.lanes,
            counting_lines=config.counting_lines,
            restricted_zones=config.restricted_zones,
            min_displacement_px=config.min_displacement_px,
            min_observation_frames=config.min_observation_frames,
        )

        events: List[TrafficEvent] = []
        timeline: List[Dict[str, Any]] = []
        violations_active_ids: Set[int] = set()

        frame_idx = 0
        analyzed_frames_count = 0
        total_frame_detections = 0
        per_frame_vehicle_counts: List[int] = []

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % sample_stride != 0:
                    frame_idx += 1
                    continue

                analyzed_frames_count += 1
                timestamp_sec = round(frame_idx / fps, 3)

                # 1. Run YOLO inference with tracker persistence
                # Ultralytics track call
                results = self.detector.model.track(
                    frame,
                    persist=True,
                    tracker="bytetrack.yaml",
                    conf=config.confidence_threshold,
                    classes=self.detector.traffic_class_ids,
                    verbose=False,
                    device=self.detector.device,
                )

                current_detections: List[BoundingBox] = []
                frame_vehicles_count = 0
                frame_pedestrians_count = 0

                if results and len(results) > 0 and results[0].boxes is not None:
                    boxes = results[0].boxes
                    xyxy = boxes.xyxy.cpu().numpy()
                    confs = boxes.conf.cpu().numpy()
                    classes = boxes.cls.cpu().numpy().astype(int)
                    track_ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else None

                    for i in range(len(xyxy)):
                        cid = int(classes[i])
                        raw_name = self.detector.model_names.get(cid, "unknown")
                        mapped_label = self.detector.map_class_id(cid, raw_name)
                        if not mapped_label:
                            continue

                        conf = float(confs[i])
                        tid = int(track_ids[i]) if track_ids is not None and i < len(track_ids) else None

                        x1 = max(0.0, min(float(xyxy[i][0]), float(width - 1)))
                        y1 = max(0.0, min(float(xyxy[i][1]), float(height - 1)))
                        x2 = max(x1 + 1.0, min(float(xyxy[i][2]), float(width)))
                        y2 = max(y1 + 1.0, min(float(xyxy[i][3]), float(height)))

                        bbox_obj = BoundingBox(
                            x1=round(x1, 1),
                            y1=round(y1, 1),
                            x2=round(x2, 1),
                            y2=round(y2, 1),
                            confidence=round(conf, 4),
                            class_name=mapped_label,
                            model_class_id=cid,
                            track_id=tid,
                            frame_number=frame_idx,
                            timestamp_seconds=timestamp_sec,
                        )
                        current_detections.append(bbox_obj)

                    # Associate riders to prevent counting two-wheeler riders as independent pedestrians
                    DetectorService.associate_riders(current_detections)

                    for bbox_obj in current_detections:
                        total_frame_detections += 1
                        if bbox_obj.is_rider:
                            pass  # Rider accounted for with two-wheeler
                        elif bbox_obj.class_name in SUPPORTED_VEHICLE_CLASSES:
                            frame_vehicles_count += 1
                        elif bbox_obj.class_name in PEDESTRIAN_CLASSES:
                            frame_pedestrians_count += 1

                        tid = bbox_obj.track_id
                        # Update tracker state if ID is assigned
                        if tid is not None:
                            entity = tracker_mgr.update_track(
                                track_id=tid,
                                class_name=bbox_obj.class_name,
                                bbox=(bbox_obj.x1, bbox_obj.y1, bbox_obj.x2, bbox_obj.y2),
                                confidence=bbox_obj.confidence,
                                frame_idx=frame_idx,
                                timestamp_seconds=timestamp_sec,
                                is_rider=bbox_obj.is_rider,
                                associated_vehicle=bbox_obj.associated_vehicle,
                            )

                            # 2. Evaluate Wrong-Side Movement
                            if not entity.wrong_side_event_emitted:
                                is_wrong, reason, cos_sim = rules_engine.evaluate_wrong_side(entity, width, height)
                                if is_wrong:
                                    entity.wrong_side_event_emitted = True
                                    violations_active_ids.add(tid)
                                    ev_id = f"EV-WS-{analysis_id}-{tid}"

                                    # Save evidence crop
                                    evidence_filename = f"evidence_{ev_id}.jpg"
                                    evidence_path = EVIDENCE_DIR / evidence_filename
                                    crop_y1 = max(0, int(bbox_obj.y1) - 10)
                                    crop_y2 = min(height, int(bbox_obj.y2) + 10)
                                    crop_x1 = max(0, int(bbox_obj.x1) - 10)
                                    crop_x2 = min(width, int(bbox_obj.x2) + 10)
                                    crop_img = frame[crop_y1:crop_y2, crop_x1:crop_x2]
                                    if crop_img.size > 0:
                                        cv2.imwrite(str(evidence_path), crop_img)
                                        ev_url = f"/static/evidence/{evidence_filename}"
                                    else:
                                        ev_url = None

                                    events.append(
                                        TrafficEvent(
                                            id=ev_id,
                                            event_type="wrong_side",
                                            severity="critical",
                                            description=f"Potential opposite-direction driving by vehicle #{tid} ({entity.dominant_class}).",
                                            timestamp_seconds=timestamp_sec,
                                            frame_number=frame_idx,
                                            track_id=tid,
                                            vehicle_type=entity.dominant_class,
                                            rule_name="Direction of Travel",
                                            reason=reason,
                                            evidence_url=ev_url,
                                        )
                                    )

                            # 3. Evaluate Lane Violations & Restricted Zones
                            if not entity.lane_violation_emitted:
                                lane_viols = rules_engine.evaluate_lane_violations(entity, width, height)
                                if lane_viols:
                                    entity.lane_violation_emitted = True
                                    violations_active_ids.add(tid)
                                    for v_type, v_reason in lane_viols:
                                        ev_id = f"EV-LN-{analysis_id}-{tid}-{len(events)}"
                                        events.append(
                                            TrafficEvent(
                                                id=ev_id,
                                                event_type=v_type,
                                                severity="warning",
                                                description=v_reason,
                                                timestamp_seconds=timestamp_sec,
                                                frame_number=frame_idx,
                                                track_id=tid,
                                                vehicle_type=entity.dominant_class,
                                                rule_name="Lane Discipline",
                                                reason=v_reason,
                                                evidence_url=None,
                                            )
                                        )

                            # 4. Evaluate Virtual Counting Line Crossings
                            rules_engine.check_counting_lines(entity, width, height)

                per_frame_vehicle_counts.append(frame_vehicles_count)

                # 5. Check Stationary Vehicle Anomalies
                active_entities = [tracker_mgr.get_entity(d.track_id) for d in current_detections if d.track_id]
                active_entities = [e for e in active_entities if e is not None]
                stopped_vehicles = CongestionAnalyzer.detect_stationary_vehicles(active_entities)
                for st_entity, st_reason in stopped_vehicles:
                    ev_id = f"EV-ST-{analysis_id}-{st_entity.track_id}"
                    events.append(
                        TrafficEvent(
                            id=ev_id,
                            event_type="stopped_vehicle",
                            severity="warning",
                            description=f"Stationary vehicle alert on vehicle #{st_entity.track_id}.",
                            timestamp_seconds=timestamp_sec,
                            frame_number=frame_idx,
                            track_id=st_entity.track_id,
                            vehicle_type=st_entity.dominant_class,
                            rule_name="Stationary Flow Obstruction",
                            reason=st_reason,
                            evidence_url=None,
                        )
                    )

                # 6. Congestion & Pedestrian metrics for current frame
                frame_cong = CongestionAnalyzer.calculate_congestion(
                    current_detections, width, height, road_roi=config.road_roi
                )

                timeline.append({
                    "frame": frame_idx,
                    "timestamp": timestamp_sec,
                    "vehicles": frame_vehicles_count,
                    "pedestrians": frame_pedestrians_count,
                    "congestion_occupancy": frame_cong.occupancy_ratio,
                    "congestion_level": frame_cong.level,
                })

                # 7. Annotate Frame with trajectories and tags
                annotated_frame = frame.copy()

                # Draw track trajectories
                for d in current_detections:
                    if d.track_id and d.track_id in tracker_mgr.tracks:
                        hist = tracker_mgr.tracks[d.track_id].history
                        if len(hist) >= 2:
                            pts = np.array([[int(p.x), int(p.y)] for p in hist[-15:]], np.int32)
                            pts = pts.reshape((-1, 1, 2))
                            t_color = (40, 40, 235) if (d.track_id in violations_active_ids) else (240, 180, 50)
                            cv2.polylines(annotated_frame, [pts], False, t_color, 2, cv2.LINE_AA)

                # Draw detections and overlays
                annotated_frame = DetectorService.annotate_image(
                    image=annotated_frame,
                    detections=current_detections,
                    road_roi=config.road_roi,
                    lanes=config.lanes,
                    counting_lines=config.counting_lines,
                    highlight_violations=violations_active_ids,
                )

                # Stamp HUD on top-left
                cv2.rectangle(annotated_frame, (10, 10), (330, 85), (20, 20, 25), -1)
                cv2.putText(
                    annotated_frame,
                    f"Vehicles (Frame): {frame_vehicles_count} | Pedestrians: {frame_pedestrians_count}",
                    (20, 32),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (240, 240, 240),
                    1,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    annotated_frame,
                    f"Flow Congestion: {frame_cong.level} ({frame_cong.occupancy_ratio*100:.1f}%)",
                    (20, 52),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (80, 220, 100) if frame_cong.level == "Low" else (50, 180, 240) if frame_cong.level == "Moderate" else (40, 60, 240),
                    1,
                    cv2.LINE_AA,
                )
                cv2.putText(
                    annotated_frame,
                    f"Active Events: {len(events)} | Time: {timestamp_sec:.1f}s",
                    (20, 72),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (200, 200, 200),
                    1,
                    cv2.LINE_AA,
                )

                out_writer.write(annotated_frame)
                frame_idx += 1

                # Progress notification
                if progress_callback and total_frames > 0:
                    pct = min(99, int((frame_idx / total_frames) * 100))
                    progress_callback(pct, f"Processing frame {frame_idx}/{total_frames} ({pct}% complete)")

        finally:
            cap.release()
            out_writer.release()

        # Transcode raw video to browser-playable H.264 (avc1) / yuv420p / +faststart via FFmpeg
        if raw_output_path.exists() and raw_output_path.stat().st_size > 0:
            ffmpeg_cmd = [
                "ffmpeg", "-y",
                "-i", str(raw_output_path),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "veryfast",
                "-crf", "23",
                "-movflags", "+faststart",
                str(output_video_path),
            ]
            try:
                res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True, timeout=180)
                if res.returncode == 0 and output_video_path.exists() and output_video_path.stat().st_size > 0:
                    raw_output_path.unlink(missing_ok=True)
                else:
                    if not output_video_path.exists() or output_video_path.stat().st_size == 0:
                        shutil.copyfile(raw_output_path, output_video_path)
            except Exception as e:
                print(f"FFmpeg transcode notice: {e}")
                if not output_video_path.exists() or output_video_path.stat().st_size == 0:
                    shutil.copyfile(raw_output_path, output_video_path)

        proc_time = round(time.time() - start_time, 2)

        # Final Aggregations
        unique_veh_total, unique_by_class, unique_peds = tracker_mgr.get_unique_vehicle_metrics()
        counting_results = rules_engine.get_counting_line_results()

        # Class counts breakdown for unique tracked entities
        total_entities = max(1, sum(unique_by_class.values()))
        class_counts_list: List[ClassCount] = []
        for cname, count in sorted(unique_by_class.items(), key=lambda x: -x[1]):
            pct = round((count / total_entities) * 100.0, 1)
            class_counts_list.append(ClassCount(class_name=cname, count=count, percentage=pct))

        peak_v = max(per_frame_vehicle_counts) if per_frame_vehicle_counts else 0
        avg_v = round(float(np.mean(per_frame_vehicle_counts)), 1) if per_frame_vehicle_counts else 0.0
        total_riders = sum(1 for e in tracker_mgr.tracks.values() if e.is_rider)

        vehicle_summary = VehicleSummary(
            unique_vehicles_total=unique_veh_total,
            unique_vehicles_by_class=unique_by_class,
            vehicles_per_frame_peak=peak_v,
            vehicles_per_frame_avg=avg_v,
            total_frame_detections=total_frame_detections,
            counting_line_results=counting_results,
            riders_associated_count=total_riders,
        )

        # Average Congestion over all analyzed frames
        avg_occupancy = float(np.mean([t["congestion_occupancy"] for t in timeline])) if timeline else 0.0
        overall_cong = CongestionAnalyzer.calculate_congestion(
            [], width, height, road_roi=config.road_roi
        )
        overall_cong.occupancy_ratio = round(avg_occupancy, 4)
        overall_cong.score = round(avg_occupancy, 3)
        if avg_occupancy < 0.20:
            overall_cong.level = "Low"
            overall_cong.description = f"Overall low road occupancy averaging {round(avg_occupancy*100, 1)}%."
        elif avg_occupancy < 0.45:
            overall_cong.level = "Moderate"
            overall_cong.description = f"Overall moderate road occupancy averaging {round(avg_occupancy*100, 1)}%."
        else:
            overall_cong.level = "High"
            overall_cong.description = f"Overall heavy congestion averaging {round(avg_occupancy*100, 1)}%."

        ped_metrics = PedestrianMetrics(
            count=int(np.mean([t["pedestrians"] for t in timeline])) if timeline else 0,
            unique_count=unique_peds,
            density_level="Low" if unique_peds <= 3 else "Moderate" if unique_peds <= 8 else "High",
            density_score=min(1.0, round(unique_peds / 10.0, 2)),
            in_crossing_zone_count=unique_peds,
            riders_excluded_count=total_riders,
            description=f"Tracked approximately {unique_peds} unique pedestrian(s) across {duration_seconds}s.",
            limitations_note="Occlusion, camera height, and lighting can affect pedestrian visibility.",
        )

        warnings: List[str] = []
        if not config.expected_direction and not config.lanes:
            warnings.append("No travel direction was configured; wrong-side movement evaluation was disabled.")
        if unique_veh_total == 0:
            warnings.append("No moving vehicles tracked with persistent IDs across observation threshold.")

        limitations: List[str] = [
            "Direction analysis reflects statistical trajectory consistency; human operator verification is required before enforcement.",
            "Vehicle speeds in km/h are not reported without metric camera calibration and perspective transformation.",
            "Standard COCO weights do not isolate Indian auto-rickshaws as a separate native class.",
        ]

        return {
            "analysis_id": analysis_id,
            "media_type": "video",
            "filename": video_path.name,
            "processing_time_seconds": proc_time,
            "video_width": width,
            "video_height": height,
            "fps": fps,
            "total_frames": total_frames,
            "frames_analyzed": analyzed_frames_count,
            "duration_seconds": duration_seconds,
            "vehicle_summary": vehicle_summary.model_dump(),
            "total_pedestrians": unique_peds,
            "unique_pedestrians": unique_peds,
            "class_counts": [cc.model_dump() for cc in class_counts_list],
            "congestion": overall_cong.model_dump(),
            "pedestrian_metrics": ped_metrics.model_dump(),
            "events": [e.model_dump() for e in events],
            "per_frame_timeline": timeline[:: max(1, len(timeline) // 50)],  # sampled down for efficient JSON transfer
            "warnings": warnings,
            "limitations": limitations,
            "annotated_media_url": f"/static/processed/{output_video_path.name}",
            "original_media_url": f"/static/uploads/{video_path.name}",
            "report_pdf_url": f"/api/reports/{analysis_id}/pdf",
            "report_csv_url": f"/api/reports/{analysis_id}/csv",
        }
