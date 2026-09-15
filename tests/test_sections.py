from app.schemas import LessonConcept, LessonContent, PracticeQuestion, WorkedExample
from app.services.content import ContentService


def test_generate_section_content_in_offline_mode(client):
    response = client.post(
        "/api/section-content",
        json={
            "topic": "Machine Learning",
            "section_title": "Core Concepts and Mental Models",
            "section_index": 1,
            "difficulty": "medium",
            "section_overview": "Understand how models learn patterns from data.",
            "learning_objectives": [
                "Distinguish training from inference",
                "Explain generalization",
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["cached"] is False
    assert payload["ai_generated"] is False
    assert payload["model_used"] == "offline-scaffold"
    assert "## Offline Study Scaffold" in payload["content"]
    assert "Distinguish training from inference" in payload["content"]


def test_section_content_is_cached_after_first_request(client):
    request = {
        "topic": "Python",
        "section_title": "Practical Applications",
        "section_index": 2,
        "difficulty": "easy",
    }

    first = client.post("/api/section-content", json=request)
    second = client.post("/api/section-content", json=request)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert first.json()["content"] == second.json()["content"]


def test_regeneration_replaces_cached_result(client):
    request = {
        "topic": "Databases",
        "section_title": "Common Pitfalls and Best Practices",
        "section_index": 4,
        "difficulty": "hard",
    }

    client.post("/api/section-content", json=request)
    regenerated = client.post("/api/regenerate-content", json=request)

    assert regenerated.status_code == 200
    assert regenerated.json()["cached"] is False


def test_structured_lesson_renderer_contains_learning_components():
    lesson = LessonContent(
        overview=(
            "Gradient descent is an iterative optimization method used to reduce "
            "a differentiable objective by following local slope information."
        ),
        why_it_matters=(
            "It is the optimization backbone of many machine-learning training "
            "procedures and explains how model parameters are updated."
        ),
        concepts=[
            LessonConcept(
                name=f"Concept {index}",
                explanation=(
                    "This concept explains an important mechanism in enough detail "
                    "to build an accurate mental model for the learner."
                ),
                intuition=(
                    "Think of moving downhill while repeatedly checking the local "
                    "slope before choosing the next small step."
                ),
                example=(
                    "For a one-dimensional quadratic loss, the slope determines "
                    "whether the next parameter update moves left or right."
                ),
            )
            for index in range(1, 4)
        ],
        worked_example=WorkedExample(
            problem="Minimize a simple quadratic loss using two gradient updates.",
            steps=[
                "Compute the derivative at the current parameter value.",
                "Multiply the derivative by the learning rate and update the value.",
            ],
            conclusion=(
                "The parameter moves toward the minimum when the step is stable."
            ),
        ),
        common_mistakes=[
            "Using a learning rate that is too large.",
            "Assuming every objective is convex.",
        ],
        practice_questions=[
            PracticeQuestion(
                question=(
                    f"Practice question {index}: what changes the update direction?"
                ),
                hint="Look at the sign of the gradient.",
                answer=(
                    "The sign of the gradient determines the local update direction."
                ),
            )
            for index in range(1, 4)
        ],
        key_takeaways=[
            "Gradients provide local direction information.",
            "The learning rate controls update size.",
            "Optimization behavior depends on the objective landscape.",
        ],
    )

    rendered = ContentService._lesson_to_markdown(lesson)

    assert "## Why It Matters" in rendered
    assert "## Worked Example" in rendered
    assert "## Common Mistakes" in rendered
    assert "## Practice" in rendered
    assert "## Key Takeaways" in rendered
    assert "### Question 3" in rendered
