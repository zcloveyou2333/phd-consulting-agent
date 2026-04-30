from pathlib import Path

from phd_consulting_agent.gemini_history import load_relevant_index


def test_load_relevant_index_reads_compact_rows(tmp_path: Path):
    csv_path = tmp_path / "gemini_activity_relevant_index.csv"
    csv_path.write_text(
        "id,created_at_raw,created_at_iso,task_tags,matched_keywords,attachment_count,prompt_chars,response_chars,prompt,attachment_labels\n"
        '"abc","Apr 29, 2026","2026GMT","student_profile_analysis","博士|背景","1","10","20","帮我做背景分析","cv.pdf"\n',
        encoding="utf-8",
    )

    rows = load_relevant_index(tmp_path, limit=5)

    assert rows[0]["id"] == "abc"
    assert rows[0]["task_tags"] == "student_profile_analysis"
