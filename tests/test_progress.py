def _create_guide(client):
    response = client.post(
        "/api/study-guide",
        json={"topic": "Transformers", "difficulty": "medium"},
    )
    return response.json()["topic_hash"]


def test_progress_round_trip(client):
    guide_hash = _create_guide(client)

    update = client.post(
        "/api/progress/update",
        json={
            "topic": "Transformers",
            "topic_hash": guide_hash,
            "section_index": 0,
            "completed": True,
            "study_time": 125.5,
        },
    )
    progress = client.get(f"/api/progress/{guide_hash}")

    assert update.status_code == 200
    assert progress.status_code == 200
    payload = progress.json()
    assert payload["completed_sections"] == 1
    assert payload["progress"]["0"]["completed"] is True
    assert payload["progress"]["0"]["study_time"] == 125.5


def test_progress_accumulates_study_time(client):
    guide_hash = _create_guide(client)
    body = {
        "topic": "Transformers",
        "topic_hash": guide_hash,
        "section_index": 1,
        "completed": False,
        "study_time": 10,
    }

    client.post("/api/progress/update", json=body)
    client.post("/api/progress/update", json=body)
    progress = client.get(f"/api/progress/{guide_hash}").json()

    assert progress["progress"]["1"]["study_time"] == 20
