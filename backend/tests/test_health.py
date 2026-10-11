from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] in ["healthy", "initializing"]
    assert "ready" in data
    assert "classes_supported" in data
    assert "unverified_classes" in data
    assert "version" in data
    assert "uptime_seconds" in data

    # Verify standard COCO road-user classes are represented
    classes = data["classes_supported"]
    assert "Car" in classes
    assert "Motorcycle" in classes
    assert "Bus" in classes
    assert "Truck" in classes
    assert "Bicycle" in classes
    assert "Pedestrian" in classes

    # Verify Auto-rickshaw limitation documentation is transparent
    unverified = data["unverified_classes"]
    assert any("Auto-rickshaw" in u for u in unverified)
