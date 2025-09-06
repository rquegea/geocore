from src.engines.openai import fetch_response

def test_openai_fetch_response():
    result = fetch_response("What is AI?", model="gpt-4")
    assert isinstance(result, str)
    assert len(result) > 0
