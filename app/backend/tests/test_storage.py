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
