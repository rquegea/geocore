from src.engines.serp import get_search_results

def test_serp_search_results():
    result = get_search_results("What is AI?")
    assert isinstance(result, str)
    assert len(result) > 0
