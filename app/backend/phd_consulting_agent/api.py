from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from phd_consulting_agent.config import default_config
from phd_consulting_agent.gemini_history import load_relevant_index
from phd_consulting_agent.models import CaseCreate, GeneratedOutput, StudentCase
from phd_consulting_agent.skill_contracts import SkillRequest
from phd_consulting_agent.skill_runner import MockSkillRunner
from phd_consulting_agent.storage import CaseRepository, init_db


class RunSkillBody(BaseModel):
    user_instruction: str
    selected_research_directions: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    document_text: str = ""


def create_app(database_path: Path | None = None) -> FastAPI:
    config = default_config()
    db_path = database_path or config.database_path
    init_db(db_path)
    repo = CaseRepository(db_path)
    runner = MockSkillRunner()
    app = FastAPI(title="PhD Consulting Agent")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/cases")
    def create_case(body: CaseCreate) -> StudentCase:
        return repo.create_case(body)

    @app.get("/cases")
    def list_cases() -> list[StudentCase]:
        return repo.list_cases()

    @app.get("/cases/{case_id}")
    def get_case(case_id: str) -> StudentCase:
        case = repo.get_case(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")
        return case

    @app.get("/cases/{case_id}/outputs")
    def list_outputs(case_id: str) -> list[GeneratedOutput]:
        if repo.get_case(case_id) is None:
            raise HTTPException(status_code=404, detail="Case not found")
        return repo.list_outputs(case_id)

    @app.post("/cases/{case_id}/run/{skill_name}")
    def run_skill(case_id: str, skill_name: str, body: RunSkillBody) -> GeneratedOutput:
        case = repo.get_case(case_id)
        if case is None:
            raise HTTPException(status_code=404, detail="Case not found")
        request = SkillRequest(
            case=case,
            user_instruction=body.user_instruction,
            selected_research_directions=body.selected_research_directions,
            target_regions=body.target_regions,
            document_text=body.document_text,
        )
        output = runner.run(skill_name, request)
        return repo.save_output(output)

    @app.get("/gemini/history")
    def gemini_history(limit: int = 100) -> list[dict[str, str]]:
        return load_relevant_index(config.gemini_cleaned_dir, limit=limit)

    return app


app = create_app()
