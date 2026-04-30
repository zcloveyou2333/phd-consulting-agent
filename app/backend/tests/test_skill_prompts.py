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
