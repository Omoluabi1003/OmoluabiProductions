from agent.discovery.query_builder import COUNTIES_FL, build_queries


def test_counties_complete():
    assert len(COUNTIES_FL) == 67


def test_queries_generated():
    queries = build_queries()
    assert any("Miami-Dade County" in q for _, q in queries)
    assert len(queries) > 67
