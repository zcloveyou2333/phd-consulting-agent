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
