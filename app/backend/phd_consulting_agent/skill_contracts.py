from __future__ import annotations

from pydantic import BaseModel, Field

from phd_consulting_agent.models import StudentCase


class SkillRequest(BaseModel):
    case: StudentCase
    user_instruction: str
    selected_research_directions: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    document_text: str = ""
