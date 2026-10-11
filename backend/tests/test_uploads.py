import io
import cv2
import numpy as np
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from app.main import app, sanitize_filename

client = TestClient(app)


def create_synthetic_image_bytes() -> bytes:
    """Creates a real valid JPEG image bytes with a painted vehicle block."""
    img = Image.new("RGB", (320, 240), color=(60, 60, 65))
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 0, 270, 240], fill=(80, 85, 90))
    draw.rectangle([100, 100, 150, 150], fill=(220, 140, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def test_unsupported_file_extension():
    """Non-media files must be rejected with 400 Bad Request."""
    fake_file = io.BytesIO(b"malicious script or invalid data")
    res = client.post(
        "/api/analyze/image",
        files={"file": ("exploit.exe", fake_file, "application/octet-stream")},
    )
    assert res.status_code == 400
    assert "Unsupported image format" in res.json()["detail"]


def test_corrupted_image_content():
    """A file named .jpg but containing non-image gibberish must be rejected by decoder validation."""
    garbage_bytes = io.BytesIO(b"Not a real JPEG image byte array at all")
    res = client.post(
        "/api/analyze/image",
        files={"file": ("fake_road.jpg", garbage_bytes, "image/jpeg")},
    )
    assert res.status_code == 400
    assert "Corrupted or invalid image" in res.json()["detail"]


def test_path_traversal_sanitization():
    """Path traversal sequences in filenames must be stripped safely."""
    malicious_name = "../../../../../etc/passwd"
    clean_name = sanitize_filename(malicious_name)
    assert clean_name == "passwd"
    assert "/" not in clean_name
    assert "\\" not in clean_name


def test_valid_image_upload_and_analysis():
    """A valid synthetic image is analyzed successfully by the full pipeline."""
    img_bytes = create_synthetic_image_bytes()
    res = client.post(
        "/api/analyze/image",
        files={"file": ("test_road.jpg", io.BytesIO(img_bytes), "image/jpeg")},
        data={"confidence": "0.25", "direction": "down"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["media_type"] == "image"
    assert "analysis_id" in data
    assert "vehicle_summary" in data
    assert "congestion" in data
    assert "report_pdf_url" in data
    assert "report_csv_url" in data
