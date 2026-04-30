from phd_consulting_agent.config import default_config


def test_default_config_points_to_repo_data_dirs():
    config = default_config()

    assert (config.repo_root / "AGENTS.md").exists()
    assert config.database_path.name == "phd_consulting_agent.sqlite3"
    assert config.gemini_cleaned_dir.name == "gemini_takeout"
