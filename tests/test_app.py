import copy
import os
import sys

# Ensure src/ is importable so we can import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import app as app_module
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client():
    with TestClient(app_module.app) as c:
        yield c


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(app_module.activities)
    yield
    # Restore the original activities state after each test
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original))


def test_get_activities_returns_json_and_status_200(client):
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    # Expect at least one known activity from initial dataset
    assert "Chess Club" in data


def test_signup_adds_participant_and_returns_200(client):
    email = "test_student@example.com"
    activity = "Chess Club"

    res = client.post(f"/activities/{activity}/signup", params={"email": email})
    assert res.status_code == 200
    body = res.json()
    assert "Signed up" in body.get("message", "")
    assert email in app_module.activities[activity]["participants"]


def test_signup_duplicate_returns_400(client):
    # pick an existing participant from the default data
    activity = "Chess Club"
    existing = app_module.activities[activity]["participants"][0]

    res = client.post(f"/activities/{activity}/signup", params={"email": existing})
    assert res.status_code == 400


def test_delete_removes_participant_and_returns_200(client):
    activity = "Chess Club"
    participant = app_module.activities[activity]["participants"][0]

    res = client.delete(f"/activities/{activity}/participants", params={"email": participant})
    assert res.status_code == 200
    body = res.json()
    assert "Removed" in body.get("message", "")
    assert participant not in app_module.activities[activity]["participants"]


def test_delete_nonexistent_returns_404(client):
    activity = "Chess Club"
    res = client.delete(f"/activities/{activity}/participants", params={"email": "noone@nowhere.example"})
    assert res.status_code == 404
