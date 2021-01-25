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


def test_candidate_search_1():
    params = {}
    response = client.get("/candidates", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['candidates']) == 5


def test_candidate_search_2():
    params = {
        'city_id': 9,  # Parnaíba - PI
        'experience_min': 1,
        'experience_max': 9,
        'techs': '24'  # Java
    }
    response = client.get("/candidates", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['candidates']) == 1


def test_candidate_search_3():
    params = {
        'experience_min': 12,
        'experience_max': 99,
        'techs': '50'  # Visual Basic
    }
    response = client.get("/candidates", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['candidates']) == 2
