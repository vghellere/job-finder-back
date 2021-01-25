from fastapi.testclient import TestClient
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.path.pardir,
    os.path.pardir))
from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {
        "status": 200, "message": "Everything is working fine here :D"
    }


def test_import_cadidates():
    response = client.post("/candidates/import")
    assert response.status_code == 201
    response_json = response.json()
    assert response_json['candidates_imported'] == 100
