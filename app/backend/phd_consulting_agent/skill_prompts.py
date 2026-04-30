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
