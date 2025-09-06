from src.engines.sentiment import analyze_sentiment

def test_analyze_sentiment_output_structure():
    text = "Texto de prueba neutral para verificar estructura del output."
    sentiment, emotion, confidence = analyze_sentiment(text)

    assert isinstance(sentiment, float)
    assert -1.0 <= sentiment <= 1.0

    emociones_validas = ["alegría", "tristeza", "enojo", "miedo", "sorpresa", "neutral"]
    assert isinstance(emotion, str)
    assert emotion in emociones_validas

    assert isinstance(confidence, float)
    assert 0.0 <= confidence <= 1.0

