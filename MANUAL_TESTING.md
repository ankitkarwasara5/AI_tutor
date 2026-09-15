# Manual Testing Guide

Use this after automated tests pass. The goal is to verify both application behavior and actual teaching quality.

## 1. Quality checks

```bash
ruff check .
ruff format --check .
pytest -v
```

## 2. Start Ollama

```bash
ollama serve
```

In another terminal:

```bash
ollama list
```

For the default quality-first setup, one of these is recommended:

```text
qwen3:8b
llama3.1:8b
gemma3:4b
qwen3:4b
llama3.2:3b
```

## 3. Run the app

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

Check runtime status:

```bash
curl http://127.0.0.1:8000/api/health
```

Confirm `model_available` is `true` and note `active_model`.

## 4. Curriculum-quality test

Generate:

```text
Topic: Gradient Descent
Difficulty: Medium
```

The study guide should have:

- exactly six sections
- topic-specific section titles
- non-generic prerequisites
- clear learning outcomes
- 2-5 objectives for each section
- topic-specific key concepts
- logical progression from foundations to integration

Reject the output as low quality if the six sections could be reused unchanged for almost any unrelated topic.

## 5. Lesson-quality test

Open a middle section, not only the introduction.

A full model-generated lesson should contain:

- Overview
- Why It Matters
- at least three Core Concepts
- explanation, intuition, and example for each concept
- one Worked Example with explicit steps
- Common Mistakes
- at least three Practice questions
- Hint and Answer for each question
- Key Takeaways

Check that the examples are genuinely about the topic and not generic placeholders.

## 6. Difficulty test

Generate the same topic at all three levels.

### Easy

Use:

```text
Bayes' Theorem
```

Expect plain language, definitions before jargon, intuition, and simple numerical examples.

### Medium

Expect more precise terminology and practical application.

### Hard

Expect assumptions, edge cases, deeper mechanisms, and mathematical detail where appropriate.

The three levels should differ materially, not just in vocabulary.

## 7. Regeneration test

Open a lesson and click **Regenerate**.

Confirm:

- the request succeeds
- the lesson structure remains complete
- the wording/examples change meaningfully
- the section remains aligned with its original objectives

## 8. Cache test

Open the same lesson again without regenerating.

Confirm the content badge says `Cached lesson` and the content is identical.

## 9. Progress test

- Mark one section complete.
- Return to the guide.
- Refresh the page.
- Confirm the completed section remains completed.
- Navigate between sections and confirm study time persists.

## 10. Offline-mode test

Stop Ollama and restart the FastAPI application.

Generate a new topic. The app should:

- remain healthy
- clearly display `Offline scaffold`
- generate a six-section study scaffold
- avoid pretending the scaffold is expert-generated subject content
- keep progress and navigation working

## 11. Docker test

```bash
docker build -t local-ai-learning-tutor .
docker run --rm -p 8000:8000 -e DISABLE_OLLAMA=true local-ai-learning-tutor
```

Then verify:

```bash
curl http://127.0.0.1:8000/api/health
```

## 12. Final Git checks

```bash
git status
git diff --stat
```

Do not commit generated database files, `.venv`, caches, or local `.env` files.

## Ollama recovery test

1. Start the FastAPI application while Ollama is stopped.
2. Confirm `/api/health` reports `mode: offline-fallback`.
3. Start Ollama and ensure a supported model is installed.
4. Wait at least three seconds, then generate a lesson again, or call:
   `curl -X POST http://127.0.0.1:8000/api/ollama/reconnect`.
5. Confirm `/api/health` now reports `mode: ollama` and an `active_model`.
6. Reopen a topic that previously showed an offline scaffold. It should now be
   replaced with model-generated teaching instead of returning the old cached scaffold.
