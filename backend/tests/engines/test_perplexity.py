from src.engines.perplexity import fetch_perplexity_response

def test_perplexity_fetch_response():
    result = fetch_perplexity_response("What is AI?")
    assert isinstance(result, str)
    assert len(result) > 0
