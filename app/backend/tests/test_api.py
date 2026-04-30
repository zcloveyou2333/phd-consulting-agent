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


def test_gemini_history_route_returns_list(tmp_path):
    client = TestClient(create_app(database_path=tmp_path / "api.sqlite3"))

    response = client.get("/gemini/history?limit=3")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
