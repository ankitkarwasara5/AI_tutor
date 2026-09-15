from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

from pydantic import ValidationError

from app.database import Database
from app.schemas import LessonContent, StudyGuideStructure
from app.services.ollama import OllamaService

logger = logging.getLogger(__name__)

CONTENT_VERSION = "v4"

DIFFICULTY_GUIDANCE = {
    "easy": (
        "Assume the learner is new to the subject. Use plain language, concrete "
        "analogies, short explanations, and simple examples. Define technical terms "
        "before using them. Avoid unnecessary notation and jargon."
    ),
    "medium": (
        "Assume basic familiarity. Build practical understanding with precise "
        "terminology, realistic examples, important trade-offs, and enough technical "
        "detail to apply the ideas independently."
    ),
    "hard": (
        "Assume strong foundations. Be rigorous. Include deeper mechanisms, "
        "assumptions, edge cases, trade-offs, and mathematical or implementation "
        "detail when it genuinely improves understanding."
    ),
}

TEACHER_SYSTEM_PROMPT = """You are an expert tutor and curriculum designer.
Teach for understanding, not for word count. Build correct mental models, connect
ideas to prior knowledge, use concrete examples, and expose common misconceptions.
Prefer precise explanations over motivational filler. Never invent citations,
benchmarks, historical claims, or facts you are unsure about. When a topic is
ambiguous, teach the most standard interpretation and state important assumptions.
"""


def topic_hash(topic: str, difficulty: str) -> str:
    normalized = f"{CONTENT_VERSION}::{topic.strip().lower()}::{difficulty}"
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def content_hash(topic: str, section_title: str, difficulty: str) -> str:
    normalized = (
        f"{CONTENT_VERSION}::{topic.strip().lower()}::"
        f"{section_title.strip().lower()}::{difficulty}"
    )
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class ContentService:
    def __init__(self, database: Database, ollama: OllamaService):
        self.database = database
        self.ollama = ollama

    async def get_study_guide(self, topic: str, difficulty: str) -> dict[str, Any]:
        key = topic_hash(topic, difficulty)
        cached = self.database.get_study_guide(key)
        ollama_available = await self.ollama.ensure_available()
        if cached and (cached["ai_generated"] or not ollama_available):
            return cached["structure"]

        structure: dict[str, Any] | None = None
        model_used = "offline-scaffold"
        ai_generated = False

        if ollama_available:
            try:
                await self.ollama.warm_up()
                raw = await self.ollama.chat(
                    self._study_guide_prompt(topic, difficulty),
                    num_predict=1800,
                    temperature=0.0,
                    system_prompt=TEACHER_SYSTEM_PROMPT,
                    format_schema=StudyGuideStructure.model_json_schema(),
                    think=False,
                )
                validated = StudyGuideStructure.model_validate_json(raw)
                structure = validated.model_dump()
                model_used = self.ollama.selected_model or "ollama"
                ai_generated = True
            except (ValidationError, ValueError, TypeError) as exc:
                logger.warning(
                    "Invalid study guide from model; using fallback: %s", exc
                )
            except Exception as exc:
                logger.warning("Study guide generation failed; using fallback: %s", exc)

        if structure is None:
            structure = self._fallback_study_guide(topic, difficulty)

        self.database.save_study_guide(
            topic=topic,
            difficulty=difficulty,
            topic_hash=key,
            structure=structure,
            model_used=model_used,
            ai_generated=ai_generated,
        )
        return structure

    async def get_section_content(
        self,
        *,
        topic: str,
        section_title: str,
        section_index: int,
        difficulty: str,
        section_overview: str | None = None,
        learning_objectives: list[str] | None = None,
        force_regenerate: bool = False,
    ) -> dict[str, Any]:
        key = content_hash(topic, section_title, difficulty)

        ollama_available = await self.ollama.ensure_available()
        if force_regenerate:
            self.database.delete_section_content(key)
        else:
            cached = self.database.get_section_content(key)
            if cached and (cached["ai_generated"] or not ollama_available):
                return {
                    "topic": topic,
                    "section_title": section_title,
                    "section_index": section_index,
                    "difficulty": difficulty,
                    "content": cached["content"],
                    "ai_generated": cached["ai_generated"],
                    "model_used": cached["model_used"],
                    "generation_time": "cached",
                    "cached": True,
                }
            if cached and ollama_available and not cached["ai_generated"]:
                self.database.delete_section_content(key)

        generated_content: str | None = None
        model_used = "offline-scaffold"
        ai_generated = False
        elapsed = 0.0

        if ollama_available:
            try:
                await self.ollama.warm_up()
                started = time.perf_counter()
                raw = await self.ollama.chat(
                    self._section_prompt(
                        topic=topic,
                        section_title=section_title,
                        difficulty=difficulty,
                        section_overview=section_overview,
                        learning_objectives=learning_objectives or [],
                    ),
                    num_predict=3200,
                    temperature=0.0,
                    system_prompt=TEACHER_SYSTEM_PROMPT,
                    format_schema=LessonContent.model_json_schema(),
                    think=False,
                )
                lesson = LessonContent.model_validate_json(raw)
                generated_content = self._lesson_to_markdown(lesson)
                elapsed = time.perf_counter() - started
                model_used = self.ollama.selected_model or "ollama"
                ai_generated = True
            except (ValidationError, ValueError, TypeError) as exc:
                logger.warning("Structured lesson validation failed: %s", exc)
            except Exception as exc:
                logger.warning("Structured lesson generation failed: %s", exc)

            if generated_content is None:
                try:
                    started = time.perf_counter()
                    generated_content = await self.ollama.chat(
                        self._section_markdown_retry_prompt(
                            topic=topic,
                            section_title=section_title,
                            difficulty=difficulty,
                            section_overview=section_overview,
                            learning_objectives=learning_objectives or [],
                        ),
                        num_predict=2600,
                        temperature=0.2,
                        system_prompt=TEACHER_SYSTEM_PROMPT,
                        think=False,
                    )
                    elapsed = time.perf_counter() - started
                    model_used = (
                        f"{self.ollama.selected_model}-markdown"
                        if self.ollama.selected_model
                        else "ollama-markdown"
                    )
                    ai_generated = True
                except Exception as exc:
                    logger.warning("Markdown lesson retry failed: %s", exc)

        if generated_content is None:
            generated_content = self._fallback_section_content(
                topic=topic,
                section_title=section_title,
                section_index=section_index,
                difficulty=difficulty,
                section_overview=section_overview,
                learning_objectives=learning_objectives or [],
            )

        self.database.save_section_content(
            topic=topic,
            section_title=section_title,
            section_index=section_index,
            difficulty=difficulty,
            content_hash=key,
            content=generated_content,
            model_used=model_used,
            generation_time=elapsed,
            ai_generated=ai_generated,
        )

        return {
            "topic": topic,
            "section_title": section_title,
            "section_index": section_index,
            "difficulty": difficulty,
            "content": generated_content,
            "ai_generated": ai_generated,
            "model_used": model_used,
            "generation_time": f"{elapsed:.1f}s" if elapsed else "instant",
            "cached": False,
        }

    @staticmethod
    def _study_guide_prompt(topic: str, difficulty: str) -> str:
        guidance = DIFFICULTY_GUIDANCE[difficulty]
        schema = StudyGuideStructure.model_json_schema()
        return f"""Design a coherent six-section learning path for: {topic!r}.
Difficulty: {difficulty}.

Learner guidance:
{guidance}

Curriculum requirements:
- Start from the real prerequisites needed for this topic.
- Sequence sections so each one prepares for the next.
- Avoid generic section names when topic-specific names are possible.
- Each section must have 2-5 observable learning objectives.
- Include 3-6 topic-specific key concepts per section.
- Mix conceptual understanding with practical application.
- The final section should integrate the topic rather than merely say "next steps".
- Keep the total plan realistic for self-study.
- Do not claim that the learner will master an entire field in a few hours.

Return JSON matching this schema exactly:
{schema}
"""

    @staticmethod
    def _section_prompt(
        *,
        topic: str,
        section_title: str,
        difficulty: str,
        section_overview: str | None,
        learning_objectives: list[str],
    ) -> str:
        guidance = DIFFICULTY_GUIDANCE[difficulty]
        overview = section_overview or "No section overview was supplied."
        objectives = "\n".join(f"- {item}" for item in learning_objectives)
        if not objectives:
            objectives = "- Build accurate understanding and practical intuition."
        schema = LessonContent.model_json_schema()

        return f"""Create one high-quality lesson inside a larger study guide.

Course topic: {topic}
Section: {section_title}
Difficulty: {difficulty}
Section overview: {overview}
Learning objectives:
{objectives}

Teaching style:
{guidance}

Lesson requirements:
- Directly teach the section title; do not give generic study advice.
- Explain at least three genuinely topic-specific concepts.
- For each concept, provide explanation, intuition, and a concrete example.
- Build one worked example from problem to conclusion in explicit steps.
- Include mistakes that learners actually make for this subject.
- Include at least three practice questions with useful hints and answers.
- Make the practice questions test understanding, not simple recall.
- Use formulas, pseudocode, code, or calculations only when relevant.
- If code is used, keep snippets small and explain what they demonstrate.
- Avoid repeating the same point in multiple sections.
- Avoid filler such as "this topic is important in today's world."
- Do not fabricate references or pretend to have verified current facts.

Return JSON matching this schema exactly:
{schema}
"""

    @staticmethod
    def _section_markdown_retry_prompt(
        *,
        topic: str,
        section_title: str,
        difficulty: str,
        section_overview: str | None,
        learning_objectives: list[str],
    ) -> str:
        guidance = DIFFICULTY_GUIDANCE[difficulty]
        overview = section_overview or "No section overview was supplied."
        objectives = "\n".join(f"- {item}" for item in learning_objectives)
        if not objectives:
            objectives = "- Build accurate understanding and practical intuition."

        return f"""Teach this lesson directly in Markdown.

Course topic: {topic}
Section: {section_title}
Difficulty: {difficulty}
Section overview: {overview}
Learning objectives:
{objectives}

Teaching style:
{guidance}

Use exactly these major sections:
## Overview
## Why It Matters
## Core Concepts
## Worked Example
## Common Mistakes
## Practice
## Key Takeaways

Requirements:
- Teach the actual subject matter, not study advice.
- Explain at least three topic-specific concepts.
- Give concrete examples and one step-by-step worked example.
- Include at least three practice questions with hints and answers.
- Include relevant formulas, pseudocode, or code when useful.
- Avoid generic filler and unsupported claims.
- Make the lesson self-contained and useful without external sources.
"""

    @staticmethod
    def _lesson_to_markdown(lesson: LessonContent) -> str:
        parts = [
            "## Overview",
            lesson.overview,
            "",
            "## Why It Matters",
            lesson.why_it_matters,
            "",
            "## Core Concepts",
        ]

        for index, concept in enumerate(lesson.concepts, start=1):
            parts.extend(
                [
                    "",
                    f"### {index}. {concept.name}",
                    concept.explanation,
                    "",
                    f"**Intuition:** {concept.intuition}",
                    "",
                    f"**Example:** {concept.example}",
                ]
            )

        parts.extend(
            [
                "",
                "## Worked Example",
                lesson.worked_example.problem,
            ]
        )
        for index, step in enumerate(lesson.worked_example.steps, start=1):
            parts.append(f"{index}. {step}")
        parts.extend(
            [
                "",
                f"**Conclusion:** {lesson.worked_example.conclusion}",
                "",
                "## Common Mistakes",
            ]
        )
        parts.extend(f"- {item}" for item in lesson.common_mistakes)

        parts.extend(["", "## Practice"])
        for index, item in enumerate(lesson.practice_questions, start=1):
            parts.extend(
                [
                    "",
                    f"### Question {index}",
                    item.question,
                    f"**Hint:** {item.hint}",
                    f"**Answer:** {item.answer}",
                ]
            )

        parts.extend(["", "## Key Takeaways"])
        parts.extend(f"- {item}" for item in lesson.key_takeaways)
        return "\n".join(parts)

    @staticmethod
    def _fallback_study_guide(topic: str, difficulty: str) -> dict[str, Any]:
        titles = [
            f"Orientation and Prerequisites for {topic}",
            f"Fundamental Ideas in {topic}",
            f"How {topic} Works",
            f"Applying {topic} to Problems",
            f"Failure Modes and Trade-offs in {topic}",
            f"Integrating and Extending {topic}",
        ]
        sections = []
        for index, title in enumerate(titles, start=1):
            sections.append(
                {
                    "id": index,
                    "title": title,
                    "overview": (
                        f"A guided {difficulty}-level scaffold for {title.lower()}. "
                        "A local model will replace this scaffold with "
                        "topic-specific curriculum content."
                    ),
                    "learning_objectives": [
                        f"Explain the purpose of this part of {topic}",
                        "Connect the ideas to the previous section",
                        "Apply the section to a concrete problem",
                    ],
                    "key_concepts": [
                        "definitions",
                        "mechanisms",
                        "application",
                    ],
                    "estimated_time": "30 min",
                }
            )
        return {
            "topic": topic,
            "difficulty": difficulty,
            "overview": (
                f"A six-part {difficulty}-level study scaffold for {topic}. "
                "Ollama is unavailable, so detailed subject teaching is disabled "
                "rather than replaced with invented generic facts."
            ),
            "prerequisites": [
                "Basic terminology related to the topic",
                "Willingness to work through examples and practice questions",
            ],
            "learning_outcomes": [
                f"Build a structured mental model of {topic}",
                f"Apply {topic} concepts to representative problems",
                "Recognize important assumptions, mistakes, and trade-offs",
            ],
            "estimated_time": "3 hours",
            "sections": sections,
        }

    @staticmethod
    def _fallback_section_content(
        *,
        topic: str,
        section_title: str,
        section_index: int,
        difficulty: str,
        section_overview: str | None,
        learning_objectives: list[str],
    ) -> str:
        objective_lines = learning_objectives or [
            f"Explain the role of {section_title} within {topic}",
            "Apply the section to a concrete example",
        ]
        overview = section_overview or (
            f"This is section {section_index + 1} of the {difficulty} learning path."
        )

        parts = [
            "## Offline Study Scaffold",
            (
                "A local Ollama model is not currently available. To avoid "
                "presenting generic template text as expert teaching, this mode "
                "provides a structured study scaffold instead."
            ),
            "",
            "## Section Goal",
            f"**Topic:** {topic}",
            f"**Section:** {section_title}",
            overview,
            "",
            "## Learning Objectives",
        ]
        parts.extend(f"- {item}" for item in objective_lines)
        parts.extend(
            [
                "",
                "## Active Study Prompts",
                (
                    f"- Define the three most important ideas in {section_title} "
                    "using a trusted textbook, course, or documentation source."
                ),
                (
                    f"- Find one concrete example of {section_title} in {topic} "
                    "and explain it step by step."
                ),
                "- Identify one assumption and one failure mode in that example.",
                "- Explain the section aloud without looking at your notes.",
                "",
                "## Practice",
                f"1. How does {section_title} connect to the larger topic of {topic}?",
                "2. Which part is easiest to misuse, and why?",
                "3. What evidence would show that you understand it in practice?",
                "",
                "## Get Full AI Teaching",
                (
                    "Start Ollama with a supported local model. The tutor will then "
                    "generate concept explanations, worked examples, mistakes, "
                    "practice questions, hints, answers, and key takeaways."
                ),
            ]
        )
        return "\n".join(parts)
