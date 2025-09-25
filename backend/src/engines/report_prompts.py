from typing import Any
import json
from . import prompts as catalog


def get_executive_summary_prompt(data: dict[str, Any]):
    """Analista Ejecutivo: KPIs y Resumen Ejecutivo.
    Usa data['corpus_for_llm'] si está presente para citar breves extractos.
    """
    corpus_note = ""
    if isinstance(data, dict) and data.get("corpus_for_llm"):
        corpus_note = f"\n\n**EXTRACTOS TEXTUALES (muestra):** {json.dumps(data.get('corpus_for_llm'), ensure_ascii=False)}\n"
    return f"""
    **ROL:** Eres un Analista Principal en una consultora estratégica de primer nivel (McKinsey, BCG). Tu audiencia es el C-suite de "The Core School". Tu lenguaje debe ser conciso, basado en datos y enfocado en el impacto de negocio.
    **TAREA:** Analiza los datos de mercado proporcionados para redactar un Resumen Ejecutivo de alto impacto que vaya directo a las conclusiones clave. No resumas los datos, interprétalos.

    **EJEMPLOS DE TONO Y ESTILO:**
    - **Headline Agudo:** "CES domina la conversación online, dejando a The Core School con una brecha de visibilidad del 49% que requiere acción inmediata."
    - **Hallazgo Profundo:** "Pérdida de Visibilidad en Temas Clave: A pesar de un sentimiento general positivo (0.62), nuestra visibilidad ha caído, especialmente en temas de alto interés como 'Carreras Audiovisuales', donde CES nos supera ampliamente."
    - **Evaluación Concluyente:** "Conclusión: Urge un cambio de estrategia. La actual estrategia de contenidos no está logrando competir eficazmente con CES. Es imperativo lanzar una campaña de posicionamiento en los temas de mayor oportunidad para revertir esta tendencia."

    **DATOS CLAVE DEL PERIODO:** {json.dumps(data, indent=2, ensure_ascii=False)}{corpus_note}

    **INSTRUCCIONES DE REDACCIÓN:**
    - Integra 1-3 citas cortas (10-25 palabras) tomadas de los extractos si aportan claridad o evidencia. No inventes citas.
    - Mantén coherencia y evita redundancias.

    **RESPONDE ÚNICAMENTE CON ESTE FORMATO JSON:**
    {{
      "executive_summary": {{
        "title": "Informe Ejecutivo de Inteligencia de Mercado y Estrategia",
        "headline": "Genera un titular de una sola frase que resuma el insight más crítico del periodo.",
        "key_findings": [
          "Hallazgo #1 sobre Visibilidad y Reputación.",
          "Hallazgo #2 sobre Posición Competitiva.",
          "Hallazgo #3 sobre Percepción de la Audiencia."
        ],
        "overall_assessment": "Evaluación general conclusiva con llamada a la acción."
      }}
    }}
    """


def get_deep_dive_analysis_prompt(data: dict[str, Any]):
    """Analista de Datos Senior: Análisis granular y correlaciones.
    Incluye extractos (si hay) para ilustrar los hallazgos.
    """
    corpus_note = ""
    if isinstance(data, dict) and data.get("corpus_for_llm"):
        corpus_note = f"\n\n**EXTRACTOS TEXTUALES (muestra):** {json.dumps(data.get('corpus_for_llm'), ensure_ascii=False)}\n"
    return f"""
    **ROL:** Eres un Analista de Datos Senior especializado en inteligencia de mercado. Tu misión es realizar un 'deep dive' en los datos granulares para descubrir insights ocultos.
    **TAREA:** Analiza las tablas desglosadas y la comparativa de sentimiento para extraer conclusiones profundas.
    **DATOS:** {json.dumps(data, indent=2, ensure_ascii=False)}{corpus_note}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "deep_dive_analysis": {{
        "title": "Análisis Profundo de Visibilidad y Sentimiento",
        "visibility_by_model": "Lectura con apoyo en datos y, si procede, breve cita",
        "visibility_by_topic": "Lectura con apoyo en datos y, si procede, breve cita",
        "sentiment_comparison": "Lectura con apoyo en datos y, si procede, breve cita"
      }}
    }}
    """


def get_recommendations_prompt(data: dict[str, Any]):
    """Estratega y Planificador: convierte insights en un plan de acción SMART.
    Puede usar citas para reforzar el porqué de cada acción.
    """
    corpus_note = ""
    if isinstance(data, dict) and data.get("corpus_for_llm"):
        corpus_note = f"\n\n**EXTRACTOS TEXTUALES (muestra):** {json.dumps(data.get('corpus_for_llm'), ensure_ascii=False)}\n"
    return f"""
    **ROL:** Eres un Consultor de Estrategia Senior de BCG/Bain. Tu trabajo es destilar todo el análisis previo en un plan de acción ejecutivo, claro y medible.

    **TAREA:** Define un Plan de Acción Estratégico con formato SMART.

    **DATOS COMPLETOS DEL ANÁLISIS:** {json.dumps(data, indent=2, ensure_ascii=False)}{corpus_note}

    **RESPONDE ÚNICAMENTE CON ESTE FORMATO JSON:**
    {{
      "strategic_action_plan": {{
        "title": "Plan de Acción Estratégico",
        "market_outlook": "Breve pronóstico basado en datos y señales cualitativas.",
        "strategic_recommendations": [
          {{
            "recommendation": "Recomendación 1",
            "details": "Justificación basada en datos y extracto si procede.",
            "kpis": "1-2 KPIs",
            "timeline": "Plazo",
            "priority": "Alta"
          }}
        ]
      }}
    }}
    """


def get_methodology_prompt():
    """Generador de texto para el apéndice."""
    return """
    **ROL:** Eres un experto en metodología de datos para una consultora.
    **TAREA:** Redacta un texto breve y claro para el apéndice de un informe que explique la metodología utilizada.
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
        "methodology": {{
            "title": "Apéndice: Metodología",
            "text": "El presente informe se basa en un análisis cuantitativo y cualitativo..."
        }}
    }}
    """


def get_correlation_anomalies_prompt(data: dict[str, Any]):
    """Analista de Correlaciones y Anomalías."""
    corpus_note = ""
    if isinstance(data, dict) and data.get("corpus_for_llm"):
        corpus_note = f"\n\n**EXTRACTOS TEXTUALES (muestra):** {json.dumps(data.get('corpus_for_llm'), ensure_ascii=False)}\n"
    return f"""
    **ROL:** Eres un Analista de Correlaciones y Anomalías. Identifica relaciones causa-efecto plausibles y anomalías.
    **DATOS ENTRADA:** {json.dumps(data, indent=2, ensure_ascii=False)}{corpus_note}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "correlation_insights": {{
        "title": "Correlaciones y Anomalías Relevantes",
        "key_correlations": [{{"pattern": "...", "evidence": "...", "confidence": "Alto"}}],
        "anomalies": [{{"signal": "...", "date": "YYYY-MM-DD", "hypothesis": "...", "next_steps": "..."}}]
      }}
    }}
    """


def get_competitive_analysis_prompt(data: dict[str, Any]):
    """Analista Competitivo: SOV, posicionamiento y debilidades."""
    corpus_note = ""
    if isinstance(data, dict) and data.get("corpus_for_llm"):
        corpus_note = f"\n\n**EXTRACTOS TEXTUALES (muestra):** {json.dumps(data.get('corpus_for_llm'), ensure_ascii=False)}\n"
    # Ejemplo de uso del catálogo central (ilustrativo; este módulo mantiene prompts complejos existentes)
    _ = catalog.IDENTIFY_COMPETITOR_WEAKNESSES.format(competitor_name="Líder", mentions_text="...")
    return f"""
    **ROL:** Eres un Analista de Inteligencia Competitiva. Tu objetivo es analizar el posicionamiento frente a competidores.

    **DATOS DE MERCADO:** {json.dumps(data, indent=2, ensure_ascii=False)}{corpus_note}

    **RESPONDE ÚNICAMENTE CON ESTE FORMATO JSON:**
    {{
      "competitive_landscape": {{
        "title": "Análisis del Panorama Competitivo",
        "overall_positioning": "Describe la posición general basada en SOV y sentimiento.",
        "leader_analysis": "Análisis del líder.",
        "competitor_weaknesses": [{{"competitor": "...", "theme": "...", "analysis": "..."}}]
      }}
    }}
    """

