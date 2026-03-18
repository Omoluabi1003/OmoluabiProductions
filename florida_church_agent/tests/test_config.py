from agent.config import get_config


def test_config_loads():
    cfg = get_config()
    assert cfg.app_name
    assert cfg.sqlite_path.name == "church_agent.db"
