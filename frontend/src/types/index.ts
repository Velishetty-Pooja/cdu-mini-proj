export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
  class_name: string;
  model_class_id: number;
  track_id?: number | null;
  frame_number?: number | null;
  timestamp_seconds?: number | null;
}

export interface ClassCount {
  class_name: string;
  count: number;
  percentage: number;
}

export interface CongestionMetrics {
  level: 'Low' | 'Moderate' | 'High';
  score: number;
  vehicle_count: number;
  occupancy_ratio: number;
  avg_speed_px_per_sec?: number | null;
  description: string;
  methodology_note: string;
}

export interface PedestrianMetrics {
  count: number;
  unique_count?: number | null;
  density_level: 'Low' | 'Moderate' | 'High';
  density_score: number;
  in_crossing_zone_count: number;
  description: string;
  limitations_note: string;
}

export interface CountingLineResult {
  line_id: string;
  line_name: string;
  forward_count: number;
  reverse_count: number;
  total_crossings: number;
}

export interface TrafficEvent {
  id: string;
  event_type: 'wrong_side' | 'lane_violation' | 'restricted_entry' | 'stopped_vehicle' | 'density_spike';
  severity: 'warning' | 'critical' | 'info';
  description: string;
  timestamp_seconds: number;
  frame_number: number;
  track_id?: number | null;
  vehicle_type?: string | null;
  rule_name: string;
  reason: string;
  evidence_url?: string | null;
}

export interface VehicleSummary {
  unique_vehicles_total: number;
  unique_vehicles_by_class: Record<string, number>;
  vehicles_per_frame_peak: number;
  vehicles_per_frame_avg: number;
  total_frame_detections: number;
  counting_line_results: CountingLineResult[];
}

export interface ImageAnalysisResponse {
  analysis_id: string;
  media_type: 'image';
  status: string;
  filename: string;
  processing_time_seconds: number;
  image_width: number;
  image_height: number;
  vehicle_summary: VehicleSummary;
  total_pedestrians: number;
  class_counts: ClassCount[];
  detections: BoundingBox[];
  congestion: CongestionMetrics;
  pedestrian_metrics: PedestrianMetrics;
  events: TrafficEvent[];
  warnings: string[];
  limitations: string[];
  annotated_media_url: string;
  original_media_url: string;
  report_pdf_url: string;
  report_csv_url: string;
}

export interface VideoJobResult {
  analysis_id: string;
  media_type: 'video';
  filename: string;
  processing_time_seconds: number;
  video_width: number;
  video_height: number;
  fps: number;
  total_frames: number;
  frames_analyzed: number;
  duration_seconds: number;
  vehicle_summary: VehicleSummary;
  total_pedestrians: number;
  unique_pedestrians: number;
  class_counts: ClassCount[];
  congestion: CongestionMetrics;
  pedestrian_metrics: PedestrianMetrics;
  events: TrafficEvent[];
  per_frame_timeline: Array<{
    frame: number;
    timestamp: number;
    vehicles: number;
    pedestrians: number;
    congestion_occupancy: number;
    congestion_level: string;
  }>;
  warnings: string[];
  limitations: string[];
  annotated_media_url: string;
  original_media_url: string;
  report_pdf_url: string;
  report_csv_url: string;
}

export interface VideoJobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress_percent: number;
  current_frame: number;
  total_frames: number;
  message: string;
  created_at: string;
  updated_at: string;
  error?: string | null;
  result?: VideoJobResult | null;
}

export interface HealthResponse {
  status: string;
  ready: boolean;
  model_name: string;
  device: string;
  classes_supported: string[];
  unverified_classes: string[];
  version: string;
  uptime_seconds: number;
}

export interface AnalysisRecordSummary {
  id: string;
  filename: string;
  media_type: 'image' | 'video';
  status: string;
  created_at: string;
  completed_at?: string | null;
  total_vehicles: number;
  total_pedestrians: number;
  events_count: number;
  congestion_level: string;
  annotated_media_url?: string | null;
  original_media_url?: string | null;
  report_pdf_url?: string | null;
  report_csv_url?: string | null;
}

export interface LaneDefinition {
  id: string;
  name: string;
  bounds: [number, number, number, number]; // [xmin, ymin, xmax, ymax] (0.0 to 1.0)
  permitted_direction: string;
  permitted_classes?: string[];
}

export interface CountingLineDefinition {
  id: string;
  name: string;
  coords: [number, number, number, number]; // [x1, y1, x2, y2] (0.0 to 1.0)
  direction_check: string;
}

export interface SampleMedia {
  name: string;
  type: 'video' | 'image';
  size_bytes: number;
  url: string;
}
