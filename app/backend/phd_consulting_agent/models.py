from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProvenanceKind(StrEnum):
    STUDENT_PROVIDED = "student_provided"
    EXTRACTED_DOCUMENT = "extracted_document"
    VERIFIED_PUBLIC = "verified_public"
    MODEL_STRATEGY = "model_strategy"
    SIMULATED_EXAMPLE = "simulated_example"


class OutputKind(StrEnum):
    BACKGROUND_ANALYSIS = "background_analysis"
    RESEARCH_DIRECTIONS = "research_directions"
    SCHOOL_SUPERVISOR_MATCHING = "school_supervisor_matching"
    COMPARABLE_CASES = "comparable_cases"
    DELIVERY_REWRITE = "delivery_rewrite"
    CALL_PREP = "call_prep"


class SourceFact(BaseModel):
    kind: ProvenanceKind
    label: str
    value: str
    source_ref: str | None = None


class CaseCreate(BaseModel):
    student_name: str = "匿名学生"
    summary: str
    target_regions: list[str] = Field(default_factory=list)
    notes: str = ""


class StudentCase(BaseModel):
    id: str = Field(default_factory=lambda: new_id("case"))
    student_name: str
    summary: str
    target_regions: list[str] = Field(default_factory=list)
    notes: str = ""
    output_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GeneratedOutput(BaseModel):
    id: str = Field(default_factory=lambda: new_id("out"))
    case_id: str
    kind: OutputKind
    title: str
    content: str
    sources: list[SourceFact] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
