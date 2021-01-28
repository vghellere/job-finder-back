from fastapi.testclient import TestClient
import sys
import os
from ..main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health-check")
    assert response.status_code == 200
    assert response.json() == {
        "status": 200, "message": "Everything is working fine here :D"
    }


def tests_import_cadidates():
    response = client.post("/management/import-s3-data")
    assert response.status_code == 201
    response_json = response.json()
    assert response_json['candidates_imported'] == 100


def test_candidate_search_1():
    params = {}
    response = client.get("/candidates", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['main_candidates']) == 5


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
    assert len(response_json['main_candidates']) == 0


def test_candidate_search_3():
    params = {
        'experience_min': 12,
        'experience_max': 99,
        'techs': '50'  # Visual Basic
    }
    response = client.get("/candidates", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['main_candidates']) == 0


def test_candidate_search_4():
    params = {
        'experience_min': 4,
        'experience_max': 10,
        'techs': '236'  # Visual Basic
    }
    response = client.get("/candidates", params=params)
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['main_candidates']) == 2
    assert len(response_json['secondary_candidates']) == 1

    candidates_main_ids = [118380, 18460]
    candidates_secondary_ids = [106140]

    for candidate in response_json['main_candidates']:
        assert candidate['id'] in candidates_main_ids

    for candidate in response_json['secondary_candidates']:
        assert candidate['id'] in candidates_secondary_ids


def test_candidate_search_options():
    response = client.get("/candidates/search-options")
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json['technologies']) > 10
    assert len(response_json['cities']) > 10
    assert response_json['experience_min'] == 0
    assert response_json['experience_max'] == 99


def test_candidate_elastic_search():
    post_data = """{"preference":"ReactiveListResult"}
{"query":{"bool":{"must":[{"bool":{"must":[{"range":{"years_experience":{"gte":0,"lte":30,"boost":2}}}]}}]}},"size":5,"_source":{"includes":["*"],"excludes":[]},"from":0}
"""

    headers = {
        'content-type': 'application/x-ndjson'
    }

    response = client.post(
        "/candidates/elastic-proxy/candidates/_msearch",
        post_data,
        headers=headers
    )

    assert response.status_code == 200
    response_json = response.json()
    response = response_json['responses'][0]
    assert response['status'] == 200
    assert response['timed_out'] is False
    assert response['hits']['total']['value'] > 0
