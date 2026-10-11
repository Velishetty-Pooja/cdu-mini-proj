import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import DATABASE_PATH


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DATABASE_PATH), timeout=20.0)
    conn.row_factory = sqlite3.Row
    return conn



def init_db():
    """Initializes SQLite database tables for analysis runs and traffic events."""
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    media_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress_percent INTEGER DEFAULT 0,
                    message TEXT,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    total_vehicles INTEGER DEFAULT 0,
                    total_pedestrians INTEGER DEFAULT 0,
                    events_count INTEGER DEFAULT 0,
                    congestion_level TEXT DEFAULT 'Low',
                    annotated_media_url TEXT,
                    original_media_url TEXT,
                    report_pdf_url TEXT,
                    report_csv_url TEXT,
                    result_json TEXT,
                    error TEXT
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS traffic_events (
                    id TEXT PRIMARY KEY,
                    analysis_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    description TEXT NOT NULL,
                    timestamp_seconds REAL NOT NULL,
                    frame_number INTEGER NOT NULL,
                    track_id INTEGER,
                    vehicle_type TEXT,
                    rule_name TEXT,
                    reason TEXT,
                    evidence_url TEXT,
                    FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
                );
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses (created_at DESC);
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_analysis_id ON traffic_events (analysis_id);
            """)
    finally:
        conn.close()


def create_analysis_record(
    analysis_id: str,
    filename: str,
    media_type: str,
    status: str = "queued",
    message: str = "Analysis queued"
) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    record = {
        "id": analysis_id,
        "filename": filename,
        "media_type": media_type,
        "status": status,
        "progress_percent": 0,
        "message": message,
        "created_at": now,
        "completed_at": None,
        "total_vehicles": 0,
        "total_pedestrians": 0,
        "events_count": 0,
        "congestion_level": "Low",
        "annotated_media_url": None,
        "original_media_url": None,
        "report_pdf_url": None,
        "report_csv_url": None,
        "result_json": None,
        "error": None
    }

    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                INSERT INTO analyses (
                    id, filename, media_type, status, progress_percent, message,
                    created_at, completed_at, total_vehicles, total_pedestrians,
                    events_count, congestion_level, annotated_media_url,
                    original_media_url, report_pdf_url, report_csv_url, result_json, error
                ) VALUES (
                    :id, :filename, :media_type, :status, :progress_percent, :message,
                    :created_at, :completed_at, :total_vehicles, :total_pedestrians,
                    :events_count, :congestion_level, :annotated_media_url,
                    :original_media_url, :report_pdf_url, :report_csv_url, :result_json, :error
                )
            """, record)
    finally:
        conn.close()

    return record


def update_analysis_progress(
    analysis_id: str,
    status: str,
    progress_percent: int,
    message: str,
    error: Optional[str] = None
):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                UPDATE analyses
                SET status = ?, progress_percent = ?, message = ?, error = ?
                WHERE id = ?
            """, (status, progress_percent, message, error, analysis_id))
    finally:
        conn.close()


def safe_extract(obj: Any, key: str, default: Any = None) -> Any:
    """Safely retrieves a property from either a dict or a Pydantic model instance."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        val = obj.get(key, default)
        return val if val is not None else default
    if hasattr(obj, key):
        val = getattr(obj, key, default)
        return val if val is not None else default
    if hasattr(obj, "model_dump"):
        dumped = obj.model_dump()
        return dumped.get(key, default)
    return default


def ensure_serializable(data: Any) -> Any:
    """Recursively converts Pydantic models to dicts for clean JSON serialization."""
    if hasattr(data, "model_dump"):
        return data.model_dump()
    if isinstance(data, dict):
        return {k: ensure_serializable(v) for k, v in data.items()}
    if isinstance(data, list):
        return [ensure_serializable(item) for item in data]
    return data


def complete_analysis_record(
    analysis_id: str,
    result_data: Any,
    events: List[Any]
):
    now = datetime.now().isoformat()
    conn = get_db_connection()
    try:
        with conn:
            # Safe extraction regardless of whether result_data / child models are dicts or Pydantic instances
            v_summary = safe_extract(result_data, "vehicle_summary", {})
            total_vehicles = safe_extract(v_summary, "unique_vehicles_total", 0)
            total_pedestrians = safe_extract(result_data, "total_pedestrians", 0)
            congestion_data = safe_extract(result_data, "congestion", {})
            congestion_level = safe_extract(congestion_data, "level", "Low")
            events_count = len(events)
            annotated_url = safe_extract(result_data, "annotated_media_url")
            original_url = safe_extract(result_data, "original_media_url")
            report_pdf_url = safe_extract(result_data, "report_pdf_url")
            report_csv_url = safe_extract(result_data, "report_csv_url")
            
            # Convert models to pure dicts for storage in SQLite result_json
            clean_result = ensure_serializable(result_data)
            result_json = json.dumps(clean_result, default=str)

            conn.execute("""
                UPDATE analyses
                SET status = 'completed',
                    progress_percent = 100,
                    message = 'Analysis complete',
                    completed_at = ?,
                    total_vehicles = ?,
                    total_pedestrians = ?,
                    events_count = ?,
                    congestion_level = ?,
                    annotated_media_url = ?,
                    original_media_url = ?,
                    report_pdf_url = ?,
                    report_csv_url = ?,
                    result_json = ?,
                    error = NULL
                WHERE id = ?
            """, (
                now, total_vehicles, total_pedestrians, events_count,
                congestion_level, annotated_url, original_url,
                report_pdf_url, report_csv_url, result_json, analysis_id
            ))

            # Insert events
            for ev in events:
                conn.execute("""
                    INSERT OR REPLACE INTO traffic_events (
                        id, analysis_id, event_type, severity, description,
                        timestamp_seconds, frame_number, track_id, vehicle_type,
                        rule_name, reason, evidence_url
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                """, (
                    ev.get("id"),
                    analysis_id,
                    ev.get("event_type", "unknown"),
                    ev.get("severity", "warning"),
                    ev.get("description", ""),
                    float(ev.get("timestamp_seconds", 0.0)),
                    int(ev.get("frame_number", 0)),
                    ev.get("track_id"),
                    ev.get("vehicle_type"),
                    ev.get("rule_name", ""),
                    ev.get("reason", ""),
                    ev.get("evidence_url")
                ))
    finally:
        conn.close()


def fail_analysis_record(analysis_id: str, error_message: str):
    conn = get_db_connection()
    try:
        with conn:
            conn.execute("""
                UPDATE analyses
                SET status = 'failed',
                    progress_percent = 100,
                    message = ?,
                    error = ?
                WHERE id = ?
            """, (f"Failed: {error_message}", error_message, analysis_id))
    finally:
        conn.close()


def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM analyses WHERE id = ?", (analysis_id,))
        row = cur.fetchone()
        if not row:
            return None
        res = dict(row)
        if res.get("result_json"):
            try:
                res["result"] = json.loads(res["result_json"])
            except Exception:
                res["result"] = None
        return res
    finally:
        conn.close()


def get_all_analyses(limit: int = 50) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, filename, media_type, status, created_at, completed_at,
                   total_vehicles, total_pedestrians, events_count, congestion_level,
                   annotated_media_url, original_media_url, report_pdf_url, report_csv_url
            FROM analyses
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_events_for_analysis(analysis_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM traffic_events
            WHERE analysis_id = ?
            ORDER BY timestamp_seconds ASC
        """, (analysis_id,))
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def delete_analysis_by_id(analysis_id: str) -> bool:
    conn = get_db_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM traffic_events WHERE analysis_id = ?", (analysis_id,))
            cur.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
            return cur.rowcount > 0
    finally:
        conn.close()


# Ensure database and tables are created automatically on load
init_db()

