import pytest
from src.engines.openai import extract_insights

def test_extract_insights_structure():
    # Texto de ejemplo simulado
    sample_text = (
        "Rho ha sido mencionada en Forbes y BuiltIn por su solución de AP Automation. "
        "Los CFOs consideran que la herramienta es útil, pero algunos piden más integración con ERPs. "
        "Las empresas deberían automatizar sus finanzas. Productos clave incluyen Corporate Cards y Expense Management."
    )

    insights = extract_insights(sample_text)

    # Verifica que sea un dict
    assert isinstance(insights, dict), "La salida no es un diccionario"

    # Campos esperados
    expected_keys = [
        "brands",
        "competitors",
        "opportunities",
        "risks",
        "pain_points",
        "trends",
        "quotes",
        "top_themes",
        "topic_frequency",
        "source_mentions",
        "calls_to_action",
        "audience_targeting",
        "products_or_features",
    ]

    for key in expected_keys:
        assert key in insights, f"Falta el campo '{key}' en el JSON"
        assert insights[key] is not None, f"El campo '{key}' es None"

    # Verifica tipos
    assert isinstance(insights["brands"], list)
    assert isinstance(insights["competitors"], list)
    assert isinstance(insights["opportunities"], list)
    assert isinstance(insights["risks"], list)
    assert isinstance(insights["pain_points"], list)
    assert isinstance(insights["trends"], list)
    assert isinstance(insights["quotes"], list)
    assert isinstance(insights["top_themes"], list)
    assert isinstance(insights["topic_frequency"], dict)
    assert isinstance(insights["source_mentions"], dict)
    assert isinstance(insights["calls_to_action"], list)
    assert isinstance(insights["audience_targeting"], list)
    assert isinstance(insights["products_or_features"], list)

