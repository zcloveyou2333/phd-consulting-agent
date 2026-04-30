# PhD Consulting Agent MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first usable local PhD consulting case workbench backed by reusable consulting skill modules.

**Architecture:** Keep the project-specific app outside the upstream `hermes-agent/` tree. Build a local FastAPI backend with SQLite persistence, a small React workbench UI, and Python skill service modules that can later be wrapped as Hermes skills. The first implementation should support the full observed consulting flow: intake, background analysis, research direction design, school/supervisor matching, comparable cases, delivery rewriting, and call prep.

**Tech Stack:** Python 3.11+, FastAPI, SQLite, Pydantic, pytest, React + Vite + TypeScript, existing Hermes skills conventions for later integration.

---

## Scope Split

This MVP spans several subsystems. Implement in this order so every stage is independently testable:

1. **Core data model and storage**: student cases, source facts, generated outputs, and provenance.
2. **Consulting skill services**: deterministic prompt builders and structured output contracts for each consulting capability.
3. **Backend API**: CRUD for cases plus endpoints that call skill services.
4. **Workbench UI**: one-page case workspace with profile, generated outputs, and rewrite/call-prep actions.
5. **Gemini history browser**: read-only reference view over cleaned Gemini data for product learning and future case retrieval.
6. **Hermes skill packaging**: wrap the service prompts into Hermes-compatible skill folders.

The first implementation should not build multi-user auth, billing, cloud deployment, or a full CRM.

## Planned File Structure

Create these project-specific paths at repo root:

- `app/backend/phd_consulting_agent/__init__.py`: package marker.
- `app/backend/phd_consulting_agent/config.py`: local paths and environment configuration.
- `app/backend/phd_consulting_agent/models.py`: Pydantic domain models and provenance enums.
- `app/backend/phd_consulting_agent/storage.py`: SQLite schema creation and repository functions.
- `app/backend/phd_consulting_agent/skill_contracts.py`: request/response models for each skill.
- `app/backend/phd_consulting_agent/skill_prompts.py`: prompt builders for each consulting workflow.
- `app/backend/phd_consulting_agent/skill_runner.py`: model-call abstraction, with a mock runner for tests.
- `app/backend/phd_consulting_agent/api.py`: FastAPI app and routes.
- `app/backend/phd_consulting_agent/gemini_history.py`: read-only helpers for cleaned Gemini JSONL/CSV data.
- `app/backend/tests/`: pytest tests for models, storage, prompt builders, API routes, and Gemini history.
- `app/frontend/package.json`: Vite React app package metadata.
- `app/frontend/src/App.tsx`: case workbench shell.
- `app/frontend/src/api.ts`: typed backend API client.
- `app/frontend/src/types.ts`: frontend case and output types.
- `app/frontend/src/components/`: focused UI components for intake, output tabs, source/provenance badges, and call prep.
- `app/frontend/src/styles.css`: restrained workbench styling.
- `skills/phd-consulting/`: Hermes skill pack folder for the consulting skills.
- `docs/product/phd-consulting-mvp.md`: product spec distilled from `AGENTS.md`.

Do not modify upstream Hermes internals until the project app and skill interfaces are proven.

---

## Task 1: Product Spec From Current Notes

**Files:**
- Create: `docs/product/phd-consulting-mvp.md`
- Read: `AGENTS.md`
- Read: `data/cleaned/gemini_takeout/summary.json`

- [ ] **Step 1: Create the product spec**

Write `docs/product/phd-consulting-mvp.md` with these sections:

```markdown
# PhD Consulting Agent MVP Product Spec

## Primary User

The first user is a PhD application consultant who prepares student-facing analysis, research direction suggestions, school/supervisor matching notes, confidence-building reference cases, and consultation call talking points.

## MVP Workflow

1. Create a student case.
2. Paste or upload student profile material.
3. Generate background analysis.
4. Generate theoretical, applied, and interdisciplinary research directions.
5. Generate school/project/supervisor matching notes for target regions.
6. Generate comparable reference cases or confidence talking points with clear provenance.
7. Rewrite output into consultant-ready Chinese narrative.
8. Generate consultation call prep notes.

## Non-Goals

- Multi-user CRM.
- Payment, auth, or SaaS deployment.
- Fully automated admissions decision-making.
- Unverified claims about current rankings, deadlines, scholarships, or supervisor availability.

## Provenance Rules

Every generated item must distinguish student-provided facts, extracted document facts, verified public facts, model-generated strategy, and simulated reference examples.

## First-Version Acceptance Criteria

- A consultant can create one case and run all MVP workflow steps locally.
- Generated outputs are saved under the case.
- The UI makes generated content easy to review, edit, and copy.
- Comparable cases are not presented as verified real cases unless their source is explicitly verified.
```

- [ ] **Step 2: Review the spec for conflict with `AGENTS.md`**

Run:

```bash
rg -n "multi-user|SaaS|verified|provenance|case workbench|Comparable" AGENTS.md docs/product/phd-consulting-mvp.md
```

Expected: output mentions both files and shows that the spec preserves the current MVP boundaries.

- [ ] **Step 3: Commit the spec**

Run:

```bash
git -C hermes-agent status --short
git status --short 2>/dev/null || true
```

Expected: root may not be a git repository; `hermes-agent` is a nested git repository. If root has no git repo, skip commit and record that this workspace currently lacks a root git repository.

---

## Task 2: Backend Project Skeleton

**Files:**
- Create: `app/backend/pyproject.toml`
- Create: `app/backend/phd_consulting_agent/__init__.py`
- Create: `app/backend/phd_consulting_agent/config.py`
- Create: `app/backend/tests/test_config.py`

- [ ] **Step 1: Write the backend package metadata**

Create `app/backend/pyproject.toml`:

```toml
[project]
name = "phd-consulting-agent-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115",
  "pydantic>=2.7",
  "uvicorn>=0.30",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
  "httpx>=0.27",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Create config module and package marker**

Create `app/backend/phd_consulting_agent/__init__.py`:

```python
"""Backend package for the PhD consulting case workbench."""
```

Create `app/backend/phd_consulting_agent/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    repo_root: Path
    data_dir: Path
    database_path: Path
    gemini_cleaned_dir: Path


def default_config() -> AppConfig:
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = repo_root / "data" / "app"
    return AppConfig(
        repo_root=repo_root,
        data_dir=data_dir,
        database_path=data_dir / "phd_consulting_agent.sqlite3",
        gemini_cleaned_dir=repo_root / "data" / "cleaned" / "gemini_takeout",
    )
```

- [ ] **Step 3: Write config test**

Create `app/backend/tests/test_config.py`:

```python
from phd_consulting_agent.config import default_config


def test_default_config_points_to_repo_data_dirs():
    config = default_config()

    assert config.repo_root.name == "phd-consulting-agent"
    assert config.database_path.name == "phd_consulting_agent.sqlite3"
    assert config.gemini_cleaned_dir.name == "gemini_takeout"
```

- [ ] **Step 4: Run the backend config test**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_config.py -v
```

Expected: `1 passed`.

---

## Task 3: Domain Models And Provenance

**Files:**
- Create: `app/backend/phd_consulting_agent/models.py`
- Create: `app/backend/tests/test_models.py`

- [ ] **Step 1: Write failing model tests**

Create `app/backend/tests/test_models.py`:

```python
from phd_consulting_agent.models import (
    CaseCreate,
    GeneratedOutput,
    OutputKind,
    ProvenanceKind,
    SourceFact,
    StudentCase,
)


def test_case_create_defaults_target_regions_to_empty_list():
    data = CaseCreate(student_name="匿名学生", summary="本科教育学，想申请港澳博士")

    assert data.target_regions == []


def test_generated_output_tracks_provenance_sources():
    output = GeneratedOutput(
        case_id="case_1",
        kind=OutputKind.BACKGROUND_ANALYSIS,
        title="背景分析",
        content="该学生的优势是硕士阶段成绩较强。",
        sources=[
            SourceFact(
                kind=ProvenanceKind.STUDENT_PROVIDED,
                label="GPA",
                value="3.8/4.0",
            )
        ],
    )

    assert output.sources[0].kind == ProvenanceKind.STUDENT_PROVIDED
    assert output.kind == OutputKind.BACKGROUND_ANALYSIS


def test_student_case_can_hold_generated_output_ids():
    case = StudentCase(
        id="case_1",
        student_name="匿名学生",
        summary="公共管理背景，目标北美全奖博士",
        target_regions=["美国", "香港"],
        output_ids=["out_1"],
    )

    assert case.output_ids == ["out_1"]
```

- [ ] **Step 2: Run model tests and verify failure**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_models.py -v
```

Expected: import failure because `phd_consulting_agent.models` is not implemented.

- [ ] **Step 3: Implement models**

Create `app/backend/phd_consulting_agent/models.py`:

```python
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
```

- [ ] **Step 4: Run model tests and verify pass**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_models.py -v
```

Expected: `3 passed`.

---

## Task 4: SQLite Storage

**Files:**
- Create: `app/backend/phd_consulting_agent/storage.py`
- Create: `app/backend/tests/test_storage.py`

- [ ] **Step 1: Write storage tests**

Create `app/backend/tests/test_storage.py`:

```python
from pathlib import Path

from phd_consulting_agent.models import CaseCreate, GeneratedOutput, OutputKind
from phd_consulting_agent.storage import CaseRepository, init_db


def test_create_and_read_case(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    init_db(db_path)
    repo = CaseRepository(db_path)

    case = repo.create_case(CaseCreate(summary="本科体育教育，目标港澳博士", target_regions=["香港", "澳门"]))
    loaded = repo.get_case(case.id)

    assert loaded is not None
    assert loaded.summary == "本科体育教育，目标港澳博士"
    assert loaded.target_regions == ["香港", "澳门"]


def test_save_output_adds_output_to_case(tmp_path: Path):
    db_path = tmp_path / "test.sqlite3"
    init_db(db_path)
    repo = CaseRepository(db_path)
    case = repo.create_case(CaseCreate(summary="公共管理背景，目标北美全奖"))

    output = repo.save_output(
        GeneratedOutput(
            case_id=case.id,
            kind=OutputKind.BACKGROUND_ANALYSIS,
            title="背景分析",
            content="硕士阶段 GPA 是核心优势。",
        )
    )
    loaded = repo.get_case(case.id)
    outputs = repo.list_outputs(case.id)

    assert loaded is not None
    assert output.id in loaded.output_ids
    assert outputs[0].content == "硕士阶段 GPA 是核心优势。"
```

- [ ] **Step 2: Run storage tests and verify failure**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_storage.py -v
```

Expected: import failure because `storage.py` is not implemented.

- [ ] **Step 3: Implement storage**

Create `app/backend/phd_consulting_agent/storage.py`:

```python
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from phd_consulting_agent.models import CaseCreate, GeneratedOutput, StudentCase, utc_now


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path) -> None:
    with connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS outputs (
                id TEXT PRIMARY KEY,
                case_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(case_id) REFERENCES cases(id)
            );
            """
        )


class CaseRepository:
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def create_case(self, data: CaseCreate) -> StudentCase:
        case = StudentCase(
            student_name=data.student_name,
            summary=data.summary,
            target_regions=data.target_regions,
            notes=data.notes,
        )
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO cases (id, payload, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (
                    case.id,
                    case.model_dump_json(),
                    case.created_at.isoformat(),
                    case.updated_at.isoformat(),
                ),
            )
        return case

    def get_case(self, case_id: str) -> StudentCase | None:
        with connect(self.db_path) as conn:
            row = conn.execute("SELECT payload FROM cases WHERE id = ?", (case_id,)).fetchone()
        if row is None:
            return None
        return StudentCase.model_validate_json(row["payload"])

    def list_cases(self) -> list[StudentCase]:
        with connect(self.db_path) as conn:
            rows = conn.execute("SELECT payload FROM cases ORDER BY created_at DESC").fetchall()
        return [StudentCase.model_validate_json(row["payload"]) for row in rows]

    def save_output(self, output: GeneratedOutput) -> GeneratedOutput:
        case = self.get_case(output.case_id)
        if case is None:
            raise ValueError(f"Case not found: {output.case_id}")

        if output.id not in case.output_ids:
            case.output_ids.append(output.id)
        case.updated_at = utc_now()

        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO outputs (id, case_id, kind, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    output.id,
                    output.case_id,
                    output.kind.value,
                    output.model_dump_json(),
                    output.created_at.isoformat(),
                ),
            )
            conn.execute(
                "UPDATE cases SET payload = ?, updated_at = ? WHERE id = ?",
                (case.model_dump_json(), case.updated_at.isoformat(), case.id),
            )
        return output

    def list_outputs(self, case_id: str) -> list[GeneratedOutput]:
        with connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT payload FROM outputs WHERE case_id = ? ORDER BY created_at ASC",
                (case_id,),
            ).fetchall()
        return [GeneratedOutput.model_validate_json(row["payload"]) for row in rows]
```

- [ ] **Step 4: Remove unused import if present**

If `json` is unused after implementation, remove `import json` from `storage.py`.

- [ ] **Step 5: Run storage tests**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_storage.py -v
```

Expected: `2 passed`.

---

## Task 5: Skill Contracts And Prompt Builders

**Files:**
- Create: `app/backend/phd_consulting_agent/skill_contracts.py`
- Create: `app/backend/phd_consulting_agent/skill_prompts.py`
- Create: `app/backend/tests/test_skill_prompts.py`

- [ ] **Step 1: Write prompt tests**

Create `app/backend/tests/test_skill_prompts.py`:

```python
from phd_consulting_agent.models import StudentCase
from phd_consulting_agent.skill_contracts import SkillRequest
from phd_consulting_agent.skill_prompts import build_prompt


def test_background_prompt_requires_provenance_labels():
    case = StudentCase(student_name="匿名学生", summary="本科财务管理 3.0，硕士公共管理 3.8，目标北美全奖博士")
    request = SkillRequest(case=case, user_instruction="帮我做背景分析")

    prompt = build_prompt("student_profile_analysis", request)

    assert "student-provided facts" in prompt
    assert "model-generated strategy" in prompt
    assert "优势" in prompt
    assert "风险" in prompt


def test_comparable_case_prompt_warns_against_fake_real_cases():
    case = StudentCase(student_name="匿名学生", summary="学生担心本科背景弱，希望增强信心")
    request = SkillRequest(case=case, user_instruction="写四个背景不如他的案例")

    prompt = build_prompt("comparable_case_generator", request)

    assert "Do not present generated examples as verified real cases" in prompt
    assert "simulated reference profiles" in prompt
```

- [ ] **Step 2: Implement skill request contract**

Create `app/backend/phd_consulting_agent/skill_contracts.py`:

```python
from __future__ import annotations

from pydantic import BaseModel, Field

from phd_consulting_agent.models import StudentCase


class SkillRequest(BaseModel):
    case: StudentCase
    user_instruction: str
    selected_research_directions: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    document_text: str = ""
```

- [ ] **Step 3: Implement prompt builders**

Create `app/backend/phd_consulting_agent/skill_prompts.py`:

```python
from __future__ import annotations

from phd_consulting_agent.skill_contracts import SkillRequest


BASE_RULES = """You are assisting a Chinese PhD application consultant.

Always separate:
- student-provided facts
- extracted document facts
- verified public facts
- model-generated strategy
- simulated examples

Write mainly in practical Chinese consulting language unless the task asks for English.
Prefer narrative output over tables unless the user asks for a table.
"""


def case_context(request: SkillRequest) -> str:
    case = request.case
    regions = request.target_regions or case.target_regions
    return f"""Student case:
- Name: {case.student_name}
- Summary: {case.summary}
- Target regions: {", ".join(regions) if regions else "未指定"}
- Notes: {case.notes or "无"}
- Document text: {request.document_text or "未提供"}
- User instruction: {request.user_instruction}
"""


def build_prompt(skill_name: str, request: SkillRequest) -> str:
    builders = {
        "student_profile_analysis": build_student_profile_analysis_prompt,
        "research_direction_design": build_research_direction_design_prompt,
        "school_supervisor_matching": build_school_supervisor_matching_prompt,
        "comparable_case_generator": build_comparable_case_generator_prompt,
        "consultant_delivery_rewriter": build_consultant_delivery_rewriter_prompt,
        "consultation_call_prep": build_consultation_call_prep_prompt,
    }
    try:
        return builders[skill_name](request)
    except KeyError as exc:
        raise ValueError(f"Unknown skill: {skill_name}") from exc


def build_student_profile_analysis_prompt(request: SkillRequest) -> str:
    return f"""{BASE_RULES}
{case_context(request)}

Task: Produce a background analysis with these sections:
1. 学术定位
2. 核心优势
3. 主要短板和风险
4. 可行申请策略
5. 需要追问学生的信息
6. 下一步建议
"""


def build_research_direction_design_prompt(request: SkillRequest) -> str:
    return f"""{BASE_RULES}
{case_context(request)}

Task: Recommend PhD research directions in three groups:
1. 理论型方向
2. 应用型方向
3. 交叉型方向

For each direction, explain fit, risk, likely departments, and how to phrase it to a student.
Respect constraints in the user instruction, especially dislikes such as avoiding quantitative, policy, education, or overly technical AI topics.
"""


def build_school_supervisor_matching_prompt(request: SkillRequest) -> str:
    directions = "\n".join(f"- {item}" for item in request.selected_research_directions) or "未选择"
    return f"""{BASE_RULES}
{case_context(request)}

Selected directions:
{directions}

Task: Produce school/project/supervisor matching notes.
Separate current verified public facts from model-generated strategy.
If current rankings, deadlines, scholarships, supervisor availability, or program requirements are needed, say they require live verification before student-facing use.
"""


def build_comparable_case_generator_prompt(request: SkillRequest) -> str:
    return f"""{BASE_RULES}
{case_context(request)}

Task: Create confidence-building comparable material.
Do not present generated examples as verified real cases.
Label generated examples as simulated reference profiles unless verified historical data is provided.
Use "simulated reference profiles" and explain the strategic lesson each profile illustrates.
"""


def build_consultant_delivery_rewriter_prompt(request: SkillRequest) -> str:
    return f"""{BASE_RULES}
{case_context(request)}

Task: Rewrite the provided material into consultant-ready Chinese narrative.
Make it specific, rich, practical, and easy to send to a student on WeChat.
Avoid tables unless explicitly requested.
"""


def build_consultation_call_prep_prompt(request: SkillRequest) -> str:
    return f"""{BASE_RULES}
{case_context(request)}

Task: Create a consultation call prep pack:
1. 开场定位
2. 3-5 个核心判断
3. 学生或家长可能追问的问题
4. 建议回答
5. 必须提醒的风险和不确定性
6. 会后行动清单
"""
```

- [ ] **Step 4: Run prompt tests**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_skill_prompts.py -v
```

Expected: `2 passed`.

---

## Task 6: Mock Skill Runner

**Files:**
- Create: `app/backend/phd_consulting_agent/skill_runner.py`
- Create: `app/backend/tests/test_skill_runner.py`

- [ ] **Step 1: Write runner tests**

Create `app/backend/tests/test_skill_runner.py`:

```python
from phd_consulting_agent.models import OutputKind, StudentCase
from phd_consulting_agent.skill_contracts import SkillRequest
from phd_consulting_agent.skill_runner import MockSkillRunner


def test_mock_runner_returns_output_kind_for_skill():
    runner = MockSkillRunner()
    case = StudentCase(student_name="匿名学生", summary="本科教育学，目标港澳博士")
    request = SkillRequest(case=case, user_instruction="帮我做背景分析")

    output = runner.run("student_profile_analysis", request)

    assert output.case_id == case.id
    assert output.kind == OutputKind.BACKGROUND_ANALYSIS
    assert "背景分析" in output.title
    assert "Mock output" in output.content
```

- [ ] **Step 2: Implement mock runner**

Create `app/backend/phd_consulting_agent/skill_runner.py`:

```python
from __future__ import annotations

from phd_consulting_agent.models import GeneratedOutput, OutputKind, ProvenanceKind, SourceFact
from phd_consulting_agent.skill_contracts import SkillRequest
from phd_consulting_agent.skill_prompts import build_prompt


SKILL_OUTPUTS = {
    "student_profile_analysis": (OutputKind.BACKGROUND_ANALYSIS, "背景分析"),
    "research_direction_design": (OutputKind.RESEARCH_DIRECTIONS, "研究方向建议"),
    "school_supervisor_matching": (OutputKind.SCHOOL_SUPERVISOR_MATCHING, "学校/项目/导师匹配"),
    "comparable_case_generator": (OutputKind.COMPARABLE_CASES, "可比参考案例"),
    "consultant_delivery_rewriter": (OutputKind.DELIVERY_REWRITE, "顾问话术改写"),
    "consultation_call_prep": (OutputKind.CALL_PREP, "咨询电话准备包"),
}


class MockSkillRunner:
    def run(self, skill_name: str, request: SkillRequest) -> GeneratedOutput:
        if skill_name not in SKILL_OUTPUTS:
            raise ValueError(f"Unknown skill: {skill_name}")
        kind, title = SKILL_OUTPUTS[skill_name]
        prompt = build_prompt(skill_name, request)
        return GeneratedOutput(
            case_id=request.case.id,
            kind=kind,
            title=title,
            content=f"Mock output for {skill_name}.\\n\\nPrompt preview:\\n{prompt[:600]}",
            sources=[
                SourceFact(
                    kind=ProvenanceKind.MODEL_STRATEGY,
                    label="mock_runner",
                    value="This output was generated by the local mock runner.",
                )
            ],
        )
```

- [ ] **Step 3: Run runner tests**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_skill_runner.py -v
```

Expected: `1 passed`.

---

## Task 7: FastAPI Case And Skill Endpoints

**Files:**
- Create: `app/backend/phd_consulting_agent/api.py`
- Create: `app/backend/tests/test_api.py`

- [ ] **Step 1: Write API tests**

Create `app/backend/tests/test_api.py`:

```python
from fastapi.testclient import TestClient

from phd_consulting_agent.api import create_app


def test_create_case_and_run_background_analysis(tmp_path):
    client = TestClient(create_app(database_path=tmp_path / "api.sqlite3"))

    create_response = client.post(
        "/cases",
        json={
            "student_name": "匿名学生",
            "summary": "本科财务管理 3.0，硕士公共管理 3.8，目标北美全奖博士",
            "target_regions": ["美国"],
        },
    )
    assert create_response.status_code == 200
    case_id = create_response.json()["id"]

    run_response = client.post(
        f"/cases/{case_id}/run/student_profile_analysis",
        json={"user_instruction": "帮我做背景分析"},
    )
    assert run_response.status_code == 200
    assert run_response.json()["kind"] == "background_analysis"

    outputs_response = client.get(f"/cases/{case_id}/outputs")
    assert outputs_response.status_code == 200
    assert len(outputs_response.json()) == 1
```

- [ ] **Step 2: Implement API**

Create `app/backend/phd_consulting_agent/api.py`:

```python
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from phd_consulting_agent.config import default_config
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

    return app


app = create_app()
```

- [ ] **Step 3: Run API tests**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_api.py -v
```

Expected: `1 passed`.

- [ ] **Step 4: Start backend manually**

Run:

```bash
cd app/backend
python3 -m uvicorn phd_consulting_agent.api:app --reload --port 8765
```

Expected: server starts at `http://127.0.0.1:8765`. Stop it after checking `/health`.

---

## Task 8: Gemini History Read-Only Browser API

**Files:**
- Create: `app/backend/phd_consulting_agent/gemini_history.py`
- Modify: `app/backend/phd_consulting_agent/api.py`
- Create: `app/backend/tests/test_gemini_history.py`

- [ ] **Step 1: Write Gemini history tests**

Create `app/backend/tests/test_gemini_history.py`:

```python
from pathlib import Path

from phd_consulting_agent.gemini_history import load_relevant_index


def test_load_relevant_index_reads_compact_rows(tmp_path: Path):
    csv_path = tmp_path / "gemini_activity_relevant_index.csv"
    csv_path.write_text(
        "id,created_at_raw,created_at_iso,task_tags,matched_keywords,attachment_count,prompt_chars,response_chars,prompt,attachment_labels\\n"
        "abc,Apr 29,2026GMT,student_profile_analysis,博士|背景,1,10,20,帮我做背景分析,cv.pdf\\n",
        encoding="utf-8",
    )

    rows = load_relevant_index(tmp_path, limit=5)

    assert rows[0]["id"] == "abc"
    assert rows[0]["task_tags"] == "student_profile_analysis"
```

- [ ] **Step 2: Implement Gemini history helper**

Create `app/backend/phd_consulting_agent/gemini_history.py`:

```python
from __future__ import annotations

import csv
from pathlib import Path


def load_relevant_index(cleaned_dir: Path, limit: int = 100) -> list[dict[str, str]]:
    path = cleaned_dir / "gemini_activity_relevant_index.csv"
    if not path.exists():
        return []
    rows: list[dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(dict(row))
            if len(rows) >= limit:
                break
    return rows
```

- [ ] **Step 3: Add API route**

Modify `app/backend/phd_consulting_agent/api.py`:

```python
from phd_consulting_agent.gemini_history import load_relevant_index
```

Inside `create_app`, add:

```python
    @app.get("/gemini/history")
    def gemini_history(limit: int = 100) -> list[dict[str, str]]:
        return load_relevant_index(config.gemini_cleaned_dir, limit=limit)
```

- [ ] **Step 4: Run Gemini history tests**

Run:

```bash
cd app/backend
python3 -m pytest tests/test_gemini_history.py tests/test_api.py -v
```

Expected: all selected tests pass.

---

## Task 9: Frontend Workbench Skeleton

**Files:**
- Create: `app/frontend/package.json`
- Create: `app/frontend/index.html`
- Create: `app/frontend/src/types.ts`
- Create: `app/frontend/src/api.ts`
- Create: `app/frontend/src/App.tsx`
- Create: `app/frontend/src/main.tsx`
- Create: `app/frontend/src/styles.css`

- [ ] **Step 1: Create frontend package**

Create `app/frontend/package.json`:

```json
{
  "scripts": {
    "dev": "vite --host 127.0.0.1 --port 5174",
    "build": "tsc && vite build"
  },
  "dependencies": {
    "@vitejs/plugin-react": "latest",
    "vite": "latest",
    "typescript": "latest",
    "react": "latest",
    "react-dom": "latest",
    "lucide-react": "latest"
  },
  "devDependencies": {}
}
```

- [ ] **Step 2: Create typed API client**

Create `app/frontend/src/types.ts`:

```ts
export type StudentCase = {
  id: string;
  student_name: string;
  summary: string;
  target_regions: string[];
  notes: string;
  output_ids: string[];
};

export type GeneratedOutput = {
  id: string;
  case_id: string;
  kind: string;
  title: string;
  content: string;
};
```

Create `app/frontend/src/api.ts`:

```ts
import type { GeneratedOutput, StudentCase } from "./types";

const API_BASE = "http://127.0.0.1:8765";

export async function createCase(input: {
  student_name: string;
  summary: string;
  target_regions: string[];
  notes: string;
}): Promise<StudentCase> {
  const response = await fetch(`${API_BASE}/cases`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) throw new Error(`Create case failed: ${response.status}`);
  return response.json();
}

export async function runSkill(caseId: string, skillName: string, userInstruction: string): Promise<GeneratedOutput> {
  const response = await fetch(`${API_BASE}/cases/${caseId}/run/${skillName}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_instruction: userInstruction }),
  });
  if (!response.ok) throw new Error(`Run skill failed: ${response.status}`);
  return response.json();
}

export async function listOutputs(caseId: string): Promise<GeneratedOutput[]> {
  const response = await fetch(`${API_BASE}/cases/${caseId}/outputs`);
  if (!response.ok) throw new Error(`List outputs failed: ${response.status}`);
  return response.json();
}
```

- [ ] **Step 3: Create workbench UI**

Create `app/frontend/src/App.tsx`:

```tsx
import { useState } from "react";
import { Brain, FileText, MessagesSquare, School, Sparkles } from "lucide-react";
import { createCase, listOutputs, runSkill } from "./api";
import type { GeneratedOutput, StudentCase } from "./types";
import "./styles.css";

const actions = [
  ["student_profile_analysis", "背景分析", Brain],
  ["research_direction_design", "研究方向", Sparkles],
  ["school_supervisor_matching", "学校/导师", School],
  ["comparable_case_generator", "可比案例", FileText],
  ["consultant_delivery_rewriter", "顾问话术", MessagesSquare],
  ["consultation_call_prep", "电话准备", MessagesSquare],
] as const;

export default function App() {
  const [summary, setSummary] = useState("");
  const [regions, setRegions] = useState("香港,澳洲");
  const [studentCase, setStudentCase] = useState<StudentCase | null>(null);
  const [outputs, setOutputs] = useState<GeneratedOutput[]>([]);
  const [busy, setBusy] = useState(false);

  async function handleCreateCase() {
    setBusy(true);
    try {
      const created = await createCase({
        student_name: "匿名学生",
        summary,
        target_regions: regions.split(",").map((item) => item.trim()).filter(Boolean),
        notes: "",
      });
      setStudentCase(created);
      setOutputs([]);
    } finally {
      setBusy(false);
    }
  }

  async function handleRun(skillName: string, label: string) {
    if (!studentCase) return;
    setBusy(true);
    try {
      await runSkill(studentCase.id, skillName, `请生成${label}`);
      setOutputs(await listOutputs(studentCase.id));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="workspace">
      <section className="case-panel">
        <h1>PhD 咨询 Case 工作台</h1>
        <label>
          学生背景
          <textarea value={summary} onChange={(event) => setSummary(event.target.value)} />
        </label>
        <label>
          目标地区
          <input value={regions} onChange={(event) => setRegions(event.target.value)} />
        </label>
        <button disabled={!summary || busy} onClick={handleCreateCase}>创建 Case</button>
        {studentCase && <p className="case-id">当前 Case: {studentCase.id}</p>}
      </section>

      <section className="action-panel">
        {actions.map(([skillName, label, Icon]) => (
          <button key={skillName} disabled={!studentCase || busy} onClick={() => handleRun(skillName, label)}>
            <Icon size={16} />
            {label}
          </button>
        ))}
      </section>

      <section className="outputs">
        {outputs.map((output) => (
          <article key={output.id} className="output">
            <h2>{output.title}</h2>
            <pre>{output.content}</pre>
          </article>
        ))}
      </section>
    </main>
  );
}
```

Create `app/frontend/src/main.tsx`:

```tsx
import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

Create `app/frontend/index.html`:

```html
<div id="root"></div>
<script type="module" src="/src/main.tsx"></script>
```

Create `app/frontend/src/styles.css`:

```css
body {
  margin: 0;
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f6f7f9;
  color: #1f2933;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(320px, 420px) 1fr;
  gap: 16px;
  padding: 16px;
}

.case-panel,
.action-panel,
.output {
  background: #ffffff;
  border: 1px solid #d8dee7;
  border-radius: 8px;
  padding: 16px;
}

.case-panel {
  grid-row: span 2;
}

h1 {
  font-size: 22px;
  margin: 0 0 16px;
}

label {
  display: grid;
  gap: 6px;
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
}

textarea {
  min-height: 220px;
  resize: vertical;
}

textarea,
input {
  border: 1px solid #c7d0dd;
  border-radius: 6px;
  padding: 10px;
  font: inherit;
}

button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: 1px solid #1f6feb;
  border-radius: 6px;
  background: #1f6feb;
  color: #ffffff;
  min-height: 36px;
  padding: 0 12px;
  font-weight: 600;
}

button:disabled {
  opacity: 0.45;
}

.action-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.outputs {
  display: grid;
  gap: 12px;
}

.output h2 {
  font-size: 16px;
  margin: 0 0 10px;
}

.output pre {
  white-space: pre-wrap;
  margin: 0;
  line-height: 1.55;
}

.case-id {
  color: #64748b;
  font-size: 13px;
}

@media (max-width: 860px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}
```

- [ ] **Step 4: Build frontend**

Run:

```bash
cd app/frontend
npm install
npm run build
```

Expected: Vite build succeeds.

---

## Task 10: CORS And End-To-End Local Run

**Files:**
- Modify: `app/backend/pyproject.toml`
- Modify: `app/backend/phd_consulting_agent/api.py`

- [ ] **Step 1: Add CORS middleware dependency usage**

Modify `app/backend/phd_consulting_agent/api.py` imports:

```python
from fastapi.middleware.cors import CORSMiddleware
```

Inside `create_app`, after app creation:

```python
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:5174"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

- [ ] **Step 2: Run all backend tests**

Run:

```bash
cd app/backend
python3 -m pytest -v
```

Expected: all backend tests pass.

- [ ] **Step 3: Start backend and frontend**

Terminal 1:

```bash
cd app/backend
python3 -m uvicorn phd_consulting_agent.api:app --reload --port 8765
```

Terminal 2:

```bash
cd app/frontend
npm run dev
```

Expected:

- Backend at `http://127.0.0.1:8765/health`.
- Frontend at `http://127.0.0.1:5174`.
- Creating a case and running all six actions shows saved mock outputs.

---

## Task 11: Hermes Skill Pack Draft

**Files:**
- Create: `skills/phd-consulting/DESCRIPTION.md`
- Create: `skills/phd-consulting/student-profile-analysis/SKILL.md`
- Create: `skills/phd-consulting/research-direction-design/SKILL.md`
- Create: `skills/phd-consulting/school-supervisor-matching/SKILL.md`
- Create: `skills/phd-consulting/comparable-case-generator/SKILL.md`
- Create: `skills/phd-consulting/consultant-delivery-rewriter/SKILL.md`
- Create: `skills/phd-consulting/consultation-call-prep/SKILL.md`

- [ ] **Step 1: Create skill pack description**

Create `skills/phd-consulting/DESCRIPTION.md`:

```markdown
# PhD Consulting Skills

Skills for a Chinese PhD application consultant. These skills support student profile analysis, research direction design, school/supervisor matching, comparable reference cases, consultant-ready rewriting, and call preparation.
```

- [ ] **Step 2: Create one SKILL.md per module**

Each `SKILL.md` must include:

```markdown
---
name: student-profile-analysis
description: Use when analyzing a PhD applicant's background, risks, positioning, and next-step strategy.
---

# Student Profile Analysis

Analyze the student's education, grades, research, work experience, target regions, funding needs, and career goals.

Always separate student-provided facts, extracted document facts, verified public facts, model-generated strategy, and simulated examples.

Output in practical Chinese consulting language with:

1. 学术定位
2. 核心优势
3. 主要短板和风险
4. 可行申请策略
5. 需要追问学生的信息
6. 下一步建议
```

For the other five skills, use the same provenance rule and adapt the output sections from `app/backend/phd_consulting_agent/skill_prompts.py`.

- [ ] **Step 3: Check skill files exist**

Run:

```bash
find skills/phd-consulting -name 'SKILL.md' -print | sort
```

Expected: six `SKILL.md` files.

---

## Task 12: Verification Checklist

**Files:**
- Read: all files created in prior tasks.

- [ ] **Step 1: Run backend tests**

Run:

```bash
cd app/backend
python3 -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd app/frontend
npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Verify cleaned data is still readable**

Run:

```bash
python3 - <<'PY'
import json
from pathlib import Path

base = Path("data/cleaned/gemini_takeout")
for name in ["gemini_activity_relevant.jsonl", "gemini_files_manifest.jsonl"]:
    count = 0
    for line in (base / name).open(encoding="utf-8"):
        json.loads(line)
        count += 1
    print(name, count)
PY
```

Expected:

```text
gemini_activity_relevant.jsonl 3367
gemini_files_manifest.jsonl 166
```

- [ ] **Step 4: Manual smoke test**

Start backend and frontend, open `http://127.0.0.1:5174`, create a case with this sample profile:

```text
本科财务管理 GPA 3.0，硕士公共管理 GPA 3.8，有一篇三作知网论文，目标 2027 年北美相关全奖博士，希望找到交叉护理/公共管理方向。
```

Run all six action buttons.

Expected:

- Six outputs appear in the workbench.
- Outputs are saved and visible after refreshing output list.
- Comparable case output contains provenance warning language from the mock prompt preview.

---

## Self-Review Notes

- `AGENTS.md` MVP scenarios map to Tasks 3-11.
- The first implementation uses a mock runner, so it proves workflow and persistence before integrating a live model.
- Current-information verification is explicitly deferred to the school/supervisor prompt contract and must be implemented before real student-facing supervisor/ranking claims.
- Root workspace currently may not be a git repository. Commit steps should be skipped unless a root repository is initialized.

