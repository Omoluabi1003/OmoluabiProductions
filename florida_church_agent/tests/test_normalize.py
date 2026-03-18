from agent.cleaning.normalize import normalize_denomination, normalize_phone, normalize_state


def test_normalize_phone():
    assert normalize_phone("+1 (305) 555-1212") == "(305) 555-1212"


def test_normalize_state():
    assert normalize_state("Florida") == "FL"


def test_normalize_denomination():
    assert normalize_denomination("non denominational") == "Nondenominational"
