from agent.cleaning.canonicalize import canonicalize_name, canonicalize_website


def test_canonicalize_name():
    assert canonicalize_name(" First Baptist Church! ") == "first baptist church"


def test_canonicalize_website():
    assert canonicalize_website("www.example.org/") == "https://example.org"
