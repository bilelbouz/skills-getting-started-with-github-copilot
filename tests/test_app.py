from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))
    return TestClient(app_module.app)


def test_get_activities_returns_activity_data(client):
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert "Chess Club" in activities
    assert set(activities["Chess Club"]) == {
        "description",
        "schedule",
        "max_participants",
        "participants",
    }
    assert isinstance(activities["Chess Club"]["participants"], list)


def test_signup_adds_participant(client):
    # Arrange
    activity = "Soccer Club"
    email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in activities_response.json()[activity]["participants"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity.replace(' ', '%20')}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    activity = "Soccer Club"
    email = "student@example.com"
    app_module.activities[activity]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert app_module.activities[activity]["participants"].count(email) == 1


def test_delete_signup_removes_participant(client):
    # Arrange
    activity = "Soccer Club"
    email = "student@example.com"
    app_module.activities[activity]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity}"}
    assert email not in activities_response.json()[activity]["participants"]


def test_delete_signup_rejects_unknown_activity(client):
    # Arrange
    activity = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity.replace(' ', '%20')}/signup",
        params={"email": "student@example.com"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_delete_signup_rejects_unregistered_participant(client):
    # Arrange
    activity = "Soccer Club"
    email = "not-signed-up@example.com"

    # Act
    response = client.delete(
        f"/activities/{activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"