import sys
import os
import pytest

# Asegura que pueda importar src.engines
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.engines.sentiment import analyze_sentiment

def test_analyze_sentiment_positive():
    text = "Moët & Chandon is an iconic champagne brand loved around the world for its elegance and quality."
    sentiment, emotion, confidence = analyze_sentiment(text)

    assert -1.0 <= sentiment <= 1.0
    assert sentiment > 0.2, f"Sentimiento esperado > 0.2 pero fue {sentiment}"
    assert emotion in ["alegría", "tristeza", "enojo", "miedo", "sorpresa", "neutral"]
    assert 0.0 <= confidence <= 1.0

def test_analyze_sentiment_negative():
    text = "I had a terrible experience with this product. Very disappointed and upset."
    sentiment, emotion, confidence = analyze_sentiment(text)

    assert -1.0 <= sentiment <= 1.0
    assert sentiment < -0.2, f"Sentimiento esperado < -0.2 pero fue {sentiment}"
    assert emotion in ["alegría", "tristeza", "enojo", "miedo", "sorpresa", "neutral"]
    assert 0.0 <= confidence <= 1.0


def test_analyze_sentiment_uncertainty_in_spanish_is_not_positive():
    text = (
        "El 32% de los jóvenes españoles de 15 años son indecisos sobre su futuro profesional, "
        "con un aumento notable en la incertidumbre reciente."
    )
    sentiment, _, confidence = analyze_sentiment(text)
    assert sentiment <= 0.0, f"Frase con indecisión/incertidumbre no debe ser positiva (fue {sentiment})"
    assert -1.0 <= sentiment <= 1.0
    assert 0.0 <= confidence <= 1.0
