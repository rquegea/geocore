import json


def get_executive_summary_prompt(data):
    """Analista Ejecutivo: KPIs y Resumen Ejecutivo."""
    return f"""
    **ROL:** Eres un Analista Principal en una consultora estratégica de primer nivel (McKinsey, BCG). Tu audiencia es el C-suite de "The Core School". Tu lenguaje debe ser conciso, basado en datos y enfocado en el impacto de negocio.
    **TAREA:** Analiza los datos de mercado proporcionados para redactar un Resumen Ejecutivo de alto impacto que vaya directo a las conclusiones clave.
    **DATOS CLAVE:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "executive_summary": {{
        "title": "Informe Ejecutivo de Inteligencia de Mercado y Estrategia",
        "headline": "Genera un titular de una sola frase que resuma el insight más crítico del periodo. Debe ser impactante y directo.",
        "key_findings": [
          "Hallazgo #1 sobre Visibilidad y Reputación: Describe la conclusión más importante sobre nuestra visibilidad y reputación, usando datos específicos como el sentimiento promedio y la evolución temporal.",
          "Hallazgo #2 sobre Posición Competitiva: Describe la conclusión más relevante sobre nuestra posición competitiva, mencionando al competidor principal y su cuota de SOV.",
          "Hallazgo #3 sobre Percepción de la Audiencia: Describe la conclusión principal sobre la voz del mercado, contrastando los temas positivos más fuertes contra los puntos de dolor más recurrentes."
        ],
        "overall_assessment": "Ofrece una evaluación final y concluyente. ¿Hemos ganado o perdido terreno en el mercado durante este periodo y cuáles son las razones fundamentales (basadas en los datos) detrás de este cambio?"
      }}
    }}
    """


def get_deep_dive_analysis_prompt(data):
    """Analista de Datos Senior: Análisis granular y correlaciones."""
    return f"""
    **ROL:** Eres un Analista de Datos Senior especializado en inteligencia de mercado. Tu misión es realizar un 'deep dive' en los datos granulares para descubrir insights ocultos.
    **TAREA:** Analiza las tablas de datos desglosados (por Modelo de IA y por Topic) y la comparativa de sentimiento para extraer conclusiones profundas.
    **DATOS:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "deep_dive_analysis": {{
        "title": "Análisis Profundo de Visibilidad y Sentimiento",
        "visibility_by_model": "Analiza la tabla 'SOV por Modelo de IA'. ¿Hay algún modelo en el que nuestra visibilidad sea particularmente fuerte o débil? ¿Qué podría implicar esto sobre el tipo de entrenamiento de cada IA?",
        "visibility_by_topic": "Analiza la tabla 'SOV por Tema'. ¿En qué temas somos líderes de conversación y en cuáles estamos por detrás? ¿Dónde están nuestras mayores oportunidades y amenazas temáticas?",
        "sentiment_comparison": "Analiza la tabla 'Comparativa de Sentimiento'. ¿Cómo se compara nuestro sentimiento promedio con el de la competencia? ¿Somos percibidos mejor o peor? ¿Qué nos dice esto sobre nuestra reputación de marca?"
      }}
    }}
    """


def get_recommendations_prompt(data):
    """Estratega y Planificador."""
    return f"""
    **ROL:** Eres un Consultor de Estrategia Senior de BCG/Bain. Tu trabajo es destilar todo el análisis previo (incluyendo el deep dive) en un plan de acción ejecutivo.
    **TAREA:** Basándote en todo el contexto, define las perspectivas futuras y las recomendaciones estratégicas.
    **DATOS COMPLETOS:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "recommendations": {{
        "title": "Perspectivas y Recomendaciones Estratégicas",
        "market_outlook": "Basado en las tendencias y el análisis competitivo, ofrece un breve pronóstico del mercado para los próximos 6-12 meses.",
        "strategic_levers": [
          {{
            "lever_title": "Capitalizar en Oportunidad Principal: [Genera un nombre para la oportunidad más importante]",
            "description": "Explica por qué esta es la oportunidad de mayor impacto, conectándola directamente con los hallazgos del análisis de marca, mercado y el 'deep dive' por tema/modelo.",
            "recommended_actions": ["Acción de Marketing/Ventas específica y medible.", "Acción de Producto/Académica a corto plazo.", "Acción de Comunicación/PR para reforzar el posicionamiento."]
          }},
          {{
            "lever_title": "Mitigar el Riesgo más Crítico: [Genera un nombre para el riesgo más urgente]",
            "description": "Describe el riesgo más significativo y su potencial impacto negativo, basándote en los datos de debilidades y competencia.",
            "recommended_actions": ["Acción inmediata para contener el riesgo.", "Acción a medio plazo para resolver la causa raíz."]
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
            "text": "El presente informe se basa en un análisis cuantitativo y cualitativo de datos recopilados entre las fechas especificadas. Las menciones de marca y competidores se obtienen a través de consultas sistemáticas a un panel de Grandes Modelos de Lenguaje (LLMs), incluyendo GPT-4, Perplexity y otros, así como el análisis de resultados de búsqueda tradicionales (SERP).<br/><br/><b>Share of Voice (SOV):</b> Se calcula como el porcentaje de menciones de una marca sobre el total de menciones de todas las marcas analizadas en el mismo periodo.<br/><br/><b>Sentimiento:</b> Cada mención es procesada por un modelo de análisis de sentimiento que asigna una puntuación de -1 (muy negativo) a +1 (muy positivo). El sentimiento promedio representa la media de estas puntuaciones.<br/><br/><b>Extracción de Insights:</b> Un modelo de IA adicional analiza el contenido de cada mención para identificar y categorizar oportunidades, riesgos, tendencias y otros elementos de negocio relevantes."
        }}
    }}
    """


def get_correlation_anomalies_prompt(data):
    """Analista de Correlaciones y Anomalías: "descubrir lo indescubrible".

    Este analista recibe datos enriquecidos con distribuciones, correlaciones,
    solapamientos (overlaps) entre riesgos y competencia y detecciones de anomalías.
    Debe producir hallazgos contundentes y verificables con foco en causalidad plausible
    y señales tempranas.
    """
    return f"""
    **ROL:** Eres un Analista de Correlaciones y Anomalías de élite. Tu trabajo es encontrar patrones sorprendentes, contradicciones y señales no obvias que otros pasarían por alto.
    **INSTRUCCIONES:**
    - Examina correlaciones entre series (visibilidad/sentimiento vs. picos de competidores, correlación tema→sentimiento, etc.).
    - Analiza distribuciones (histograma de sentimiento, fuentes y motores) para detectar colas pesadas o sesgos.
    - Identifica solapamientos entre riesgos y menciones de competidores (por días/eventos) y su posible causalidad.
    - Prioriza insights que sean accionables y contraintuitivos. Evita obviedades.
    - Cita siempre el dato/tabla que respalda el insight (nombre de la sección/clave).

    **DATOS COMPLETOS:** {json.dumps(data, indent=2, ensure_ascii=False)}

    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "correlation_analysis": {{
        "title": "Correlaciones y Solapamientos Relevantes",
        "insights": [
          "Insight que conecte una caída de sentimiento con el pico de un competidor (cita 'correlation_events').",
          "Insight sobre un tema cuyo volumen correlaciona inversamente con el sentimiento (cita 'topic_sentiment_correlations').",
          "Insight sobre fuentes o motores que sesgan el tono (cita 'distributions')."
        ],
        "implications": [
          "Implicación estratégica #1 basada en los datos.",
          "Implicación estratégica #2 basada en los datos."
        ]
      }},
      "anomaly_analysis": {{
        "title": "Anomalías y Señales Tempranas",
        "anomalies": [
          "Anomalía concreta con fecha, métrica y magnitud (cita 'outlier_days').",
          "Otra anomalía o contradicción aparente (cita la distribución o correlación relevante)."
        ],
        "watchlist": [
          "Variables/temas a vigilar en el próximo periodo con razón específica."
        ]
      }}
    }}
    """

