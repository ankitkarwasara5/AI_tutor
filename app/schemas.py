from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]


class StudyGuideRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    difficulty: Difficulty = "medium"


class SectionContentRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    section_title: str = Field(..., min_length=3, max_length=200)
    section_index: int = Field(..., ge=0, le=10)
    difficulty: Difficulty = "medium"
    section_overview: str | None = Field(default=None, max_length=600)
    learning_objectives: list[str] = Field(default_factory=list, max_length=6)


class RegenerateContentRequest(SectionContentRequest):
    pass


class ProgressUpdateRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=100)
    topic_hash: str = Field(..., min_length=10, max_length=100)
    section_index: int = Field(..., ge=0, le=10)
    completed: bool = True
    study_time: float = Field(default=0, ge=0, le=24 * 60 * 60)


class StudySection(BaseModel):
    id: int = Field(ge=1, le=8)
    title: str = Field(min_length=3, max_length=120)
    overview: str = Field(min_length=20, max_length=500)
    learning_objectives: list[str] = Field(min_length=2, max_length=5)
    key_concepts: list[str] = Field(default_factory=list, max_length=6)
    estimated_time: str = Field(min_length=2, max_length=40)


class StudyGuideStructure(BaseModel):
    topic: str
    difficulty: Difficulty
    overview: str = Field(min_length=40, max_length=800)
    prerequisites: list[str] = Field(default_factory=list, max_length=6)
    learning_outcomes: list[str] = Field(default_factory=list, max_length=6)
    estimated_time: str
    sections: list[StudySection] = Field(min_length=6, max_length=6)


class LessonConcept(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    explanation: str = Field(min_length=40, max_length=900)
    intuition: str = Field(min_length=20, max_length=600)
    example: str = Field(min_length=20, max_length=800)


class WorkedExample(BaseModel):
    problem: str = Field(min_length=20, max_length=700)
    steps: list[str] = Field(min_length=2, max_length=8)
    conclusion: str = Field(min_length=20, max_length=700)


class PracticeQuestion(BaseModel):
    question: str = Field(min_length=10, max_length=400)
    hint: str = Field(min_length=5, max_length=300)
    answer: str = Field(min_length=10, max_length=600)


class LessonContent(BaseModel):
    overview: str = Field(min_length=60, max_length=1200)
    why_it_matters: str = Field(min_length=40, max_length=900)
    concepts: list[LessonConcept] = Field(min_length=3, max_length=6)
    worked_example: WorkedExample
    common_mistakes: list[str] = Field(min_length=2, max_length=6)
    practice_questions: list[PracticeQuestion] = Field(min_length=3, max_length=5)
    key_takeaways: list[str] = Field(min_length=3, max_length=6)
