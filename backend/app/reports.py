import csv
import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from .config import REPORTS_DIR


from .database import safe_extract, ensure_serializable


def generate_csv_report(analysis_id: str, data: Any, output_path: Path) -> Path:
    """Generates an auditable, structured CSV report for the analysis."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # 1. Header & Metadata
        writer.writerow(["=== INDIAN TRAFFIC INTELLIGENCE SYSTEM ANALYSIS REPORT ==="])
        writer.writerow(["Report Generated At", datetime.now().isoformat()])
        writer.writerow(["Analysis ID", analysis_id])
        writer.writerow(["Media Type", safe_extract(data, "media_type", "unknown")])
        writer.writerow(["Source Filename", safe_extract(data, "filename", "unknown")])
        writer.writerow(["Processing Time (s)", safe_extract(data, "processing_time_seconds", 0.0)])
        writer.writerow([])

        # 2. Executive Metrics Summary
        v_summary = safe_extract(data, "vehicle_summary", {})
        writer.writerow(["=== VEHICLE & ROAD USAGE SUMMARY ==="])
        writer.writerow(["Total Unique Vehicles Observed", safe_extract(v_summary, "unique_vehicles_total", 0)])
        writer.writerow(["Peak Vehicles Per Frame", safe_extract(v_summary, "vehicles_per_frame_peak", 0)])
        writer.writerow(["Average Vehicles Per Frame", safe_extract(v_summary, "vehicles_per_frame_avg", 0.0)])
        writer.writerow(["Total Frame Detections", safe_extract(v_summary, "total_frame_detections", 0)])
        writer.writerow(["Total Pedestrians Detected", safe_extract(data, "total_pedestrians", 0)])
        if safe_extract(data, "unique_pedestrians") is not None:
            writer.writerow(["Unique Pedestrians Tracked", safe_extract(data, "unique_pedestrians")])

        cong = safe_extract(data, "congestion", {})
        writer.writerow(["Congestion Assessment Level", safe_extract(cong, "level", "Low")])
        writer.writerow(["Road Occupancy Ratio", safe_extract(cong, "occupancy_ratio", 0.0)])
        writer.writerow([])

        # 3. Class Counts Breakdown
        writer.writerow(["=== VEHICLE & ROAD-USER CLASSIFICATION BREAKDOWN ==="])
        writer.writerow(["Class Name", "Count", "Percentage (%)"])
        for cc in data.get("class_counts", []):
            c_name = cc.get("class_name") if isinstance(cc, dict) else getattr(cc, "class_name", "")
            c_count = cc.get("count") if isinstance(cc, dict) else getattr(cc, "count", 0)
            c_pct = cc.get("percentage") if isinstance(cc, dict) else getattr(cc, "percentage", 0.0)
            writer.writerow([c_name, c_count, c_pct])
        writer.writerow([])

        # 4. Counting Line Crossings
        cl_results = safe_extract(v_summary, "counting_line_results", [])
        if cl_results:
            writer.writerow(["=== VIRTUAL COUNTING LINE METRICS ==="])
            writer.writerow(["Line ID", "Line Name", "Forward Crossings", "Reverse Crossings", "Total Crossings"])
            for cl in cl_results:
                lid = safe_extract(cl, "line_id", "")
                lname = safe_extract(cl, "line_name", "")
                fwd = safe_extract(cl, "forward_count", 0)
                rev = safe_extract(cl, "reverse_count", 0)
                tot = safe_extract(cl, "total_crossings", 0)
                writer.writerow([lid, lname, fwd, rev, tot])
            writer.writerow([])

        # 5. Flagged Traffic Events
        events = safe_extract(data, "events", [])
        writer.writerow(["=== FLAGGED TRAFFIC ANOMALIES & EVENTS ==="])
        writer.writerow(["Event ID", "Timestamp (s)", "Frame", "Event Type", "Severity", "Track ID", "Vehicle Type", "Rule", "Reason"])
        for ev in events:
            eid = safe_extract(ev, "id", "")
            ts = safe_extract(ev, "timestamp_seconds", 0.0)
            fr = safe_extract(ev, "frame_number", 0)
            etype = safe_extract(ev, "event_type", "")
            sev = safe_extract(ev, "severity", "")
            tid = safe_extract(ev, "track_id", "")
            vtype = safe_extract(ev, "vehicle_type", "")
            rname = safe_extract(ev, "rule_name", "")
            reas = safe_extract(ev, "reason", "")
            writer.writerow([eid, ts, fr, etype, sev, tid, vtype, rname, reas])
        writer.writerow([])

        # 6. Scientific Limitations & Disclaimers
        writer.writerow(["=== SCIENTIFIC LIMITATIONS & LEGAL DISCLAIMERS ==="])
        for lim in safe_extract(data, "limitations", []):
            writer.writerow([lim])

    return output_path


def generate_pdf_report(analysis_id: str, data: Dict[str, Any], output_path: Path) -> Path:
    """Generates an executive, publication-ready PDF audit report using ReportLab."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        fontName="Helvetica",
    )
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=6,
    )
    body_text = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155"),
        fontName="Helvetica",
    )
    table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontSize=9,
        leading=11,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )
    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b"),
        fontName="Helvetica",
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("INDIAN TRAFFIC INTELLIGENCE SYSTEM", title_style))
    elements.append(Paragraph(f"Analysis Audit Report & Evidence Dossier | ID: <b>{analysis_id}</b>", subtitle_style))
    elements.append(Spacer(1, 8))
    elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceBefore=2, spaceAfter=8))

    # 2. Executive Overview Table
    v_summary = safe_extract(data, "vehicle_summary", {})
    cong = safe_extract(data, "congestion", {})
    events = safe_extract(data, "events", [])

    meta_table_data = [
        [
            Paragraph("<b>Source File:</b>", table_cell),
            Paragraph(str(safe_extract(data, "filename", "N/A")), table_cell),
            Paragraph("<b>Media Type:</b>", table_cell),
            Paragraph(str(safe_extract(data, "media_type", "image")).upper(), table_cell),
        ],
        [
            Paragraph("<b>Analysis Time:</b>", table_cell),
            Paragraph(f"{safe_extract(data, 'processing_time_seconds', 0.0):.2f} sec", table_cell),
            Paragraph("<b>Timestamp:</b>", table_cell),
            Paragraph(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), table_cell),
        ],
        [
            Paragraph("<b>Unique Vehicles:</b>", table_cell),
            Paragraph(str(safe_extract(v_summary, "unique_vehicles_total", 0)), table_cell),
            Paragraph("<b>Total Pedestrians:</b>", table_cell),
            Paragraph(str(safe_extract(data, "total_pedestrians", 0)), table_cell),
        ],
        [
            Paragraph("<b>Congestion Level:</b>", table_cell),
            Paragraph(f"<b>{safe_extract(cong, 'level', 'Low')}</b> ({safe_extract(cong, 'occupancy_ratio', 0.0)*100:.1f}%)", table_cell),
            Paragraph("<b>Flagged Events:</b>", table_cell),
            Paragraph(f"<b>{len(events)}</b> potential violation(s)", table_cell),
        ],
    ]

    meta_table = Table(meta_table_data, colWidths=[105, 160, 110, 165])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    # 3. Vehicle Classification Table
    elements.append(Paragraph("1. Vehicle & Road-User Class Distribution", section_title))
    class_table_rows = [
        [
            Paragraph("Road-User Class", table_header),
            Paragraph("Detected Count", table_header),
            Paragraph("Share of Volume (%)", table_header),
        ]
    ]

    class_counts = safe_extract(data, "class_counts", [])
    if class_counts:
        for cc in class_counts:
            c_name = safe_extract(cc, "class_name", "")
            c_count = safe_extract(cc, "count", 0)
            c_pct = safe_extract(cc, "percentage", 0.0)
            class_table_rows.append([
                Paragraph(c_name, table_cell),
                Paragraph(str(c_count), table_cell),
                Paragraph(f"{c_pct:.1f}%", table_cell),
            ])
    else:
        class_table_rows.append([Paragraph("No road users detected", table_cell), Paragraph("0", table_cell), Paragraph("0.0%", table_cell)])

    class_table = Table(class_table_rows, colWidths=[200, 170, 170])
    class_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(class_table)
    elements.append(Spacer(1, 10))

    # 4. Traffic Events & Direction Analysis Table
    elements.append(Paragraph("2. Flagged Potential Direction & Lane Events", section_title))
    if events:
        event_table_rows = [
            [
                Paragraph("Time", table_header),
                Paragraph("Type", table_header),
                Paragraph("Severity", table_header),
                Paragraph("Vehicle", table_header),
                Paragraph("Evidence & Explanation", table_header),
            ]
        ]
        for ev in events[:15]:  # show top 15 in summary table
            ts = safe_extract(ev, "timestamp_seconds", 0.0)
            etype = safe_extract(ev, "event_type", "")
            sev = safe_extract(ev, "severity", "")
            tid = safe_extract(ev, "track_id", "")
            vtype = safe_extract(ev, "vehicle_type", "Vehicle")
            reas = safe_extract(ev, "reason", "")

            event_table_rows.append([
                Paragraph(f"{ts:.1f}s", table_cell),
                Paragraph(etype.replace("_", " ").title(), table_cell),
                Paragraph(sev.upper(), table_cell),
                Paragraph(f"#{tid} {vtype}", table_cell),
                Paragraph(reas, table_cell),
            ])

        ev_table = Table(event_table_rows, colWidths=[45, 90, 60, 85, 260])
        ev_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#b91c1c")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fef2f2")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        elements.append(ev_table)
    else:
        elements.append(Paragraph("No directional or lane movement anomalies detected in the evaluated footage.", body_text))

    elements.append(Spacer(1, 12))

    # 5. Scientific Limitations & Legal Disclaimer
    elements.append(Paragraph("3. Scientific Limitations & Operational Disclaimers", section_title))
    limitations = safe_extract(data, "limitations", [
        "Analysis uses automated computer-vision heuristics and pretrained YOLO weights.",
        "Direction and lane events represent potential movement anomalies requiring human operator review.",
        "Auto-rickshaws and indigenous Indian road vehicles may be categorized under standard COCO classes.",
        "Physical speed in km/h is omitted due to absence of metric camera homography calibration.",
    ])
    for lim in limitations:
        elements.append(Paragraph(f"• {lim}", body_text))

    doc.build(elements)
    return output_path


def generate_reports(analysis_id: str, data: Any, reports_dir: Path = REPORTS_DIR) -> Dict[str, str]:
    """Generates both CSV and PDF reports and returns their relative download endpoints."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    clean_data = ensure_serializable(data)
    csv_file = reports_dir / f"traffic_report_{analysis_id}.csv"
    pdf_file = reports_dir / f"traffic_report_{analysis_id}.pdf"

    generate_csv_report(analysis_id, clean_data, csv_file)
    generate_pdf_report(analysis_id, clean_data, pdf_file)

    return {
        "csv_path": str(csv_file),
        "pdf_path": str(pdf_file),
        "csv_url": f"/api/reports/{analysis_id}/csv",
        "pdf_url": f"/api/reports/{analysis_id}/pdf",
    }
