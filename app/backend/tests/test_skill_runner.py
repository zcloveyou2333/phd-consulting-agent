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
