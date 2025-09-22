import json


def get_executive_summary_prompt(data):
    """Analista Ejecutivo: KPIs y Resumen Ejecutivo."""
    return f"""
    **ROL:** Eres un Analista Principal en una consultora estratégica de primer nivel (McKinsey, BCG). Tu audiencia es el C-suite de "The Core School". Tu lenguaje debe ser conciso, basado en datos y enfocado en el impacto de negocio.
    **TAREA:** Analiza los datos de mercado proporcionados para redactar un Resumen Ejecutivo de alto impacto que vaya directo a las conclusiones clave. No resumas los datos, interprétalos.

    **EJEMPLOS DE TONO Y ESTILO:**
    - **Headline Agudo:** "CES domina la conversación online, dejando a The Core School con una brecha de visibilidad del 49% que requiere acción inmediata."
    - **Hallazgo Profundo:** "Pérdida de Visibilidad en Temas Clave: A pesar de un sentimiento general positivo (0.62), nuestra visibilidad ha caído, especialmente en temas de alto interés como 'Carreras Audiovisuales', donde CES nos supera ampliamente."
    - **Evaluación Concluyente:** "Conclusión: Urge un cambio de estrategia. La actual estrategia de contenidos no está logrando competir eficazmente con CES. Es imperativo lanzar una campaña de posicionamiento en los temas de mayor oportunidad para revertir esta tendencia."

    **DATOS CLAVE DEL PERIODO:** {json.dumps(data, indent=2, ensure_ascii=False)}

    **RESPONDE ÚNICAMENTE CON ESTE FORMATO JSON:**
    {{
      "executive_summary": {{
        "title": "Informe Ejecutivo de Inteligencia de Mercado y Estrategia",
        "headline": "Genera un titular de una sola frase que resuma el insight más crítico del periodo. Debe ser impactante, directo y basado en los datos más relevantes (ej. la brecha de SOV, una caída de sentimiento, etc.).",
        "key_findings": [
          "Hallazgo #1 sobre Visibilidad y Reputación: Conecta la visibilidad y el sentimiento. Por ejemplo, si la visibilidad baja a pesar de un buen sentimiento, explícalo. Usa datos específicos.",
          "Hallazgo #2 sobre Posición Competitiva: Analiza la brecha con el líder. Menciona el nombre del competidor principal y la diferencia en SOV. Señala el área o tema donde esta brecha es más pronunciada.",
          "Hallazgo #3 sobre Percepción de la Audiencia: Contrasta el tema más positivo con el más negativo. Explica qué nos dice esto sobre lo que el mercado valora de nosotros y cuáles son sus principales preocupaciones."
        ],
        "overall_assessment": "Ofrece una evaluación final y concluyente. ¿Hemos ganado o perdido terreno en el mercado durante este periodo y cuáles son las razones fundamentales (basadas en los datos) detrás de este cambio? Termina con una frase que cree urgencia o señale el siguiente paso lógico."
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
    """Estratega y Planificador: convierte insights en un plan de acción SMART."""
    return f"""
    **ROL:** Eres un Consultor de Estrategia Senior de BCG/Bain. Tu trabajo es destilar todo el análisis previo en un plan de acción ejecutivo, claro y medible. Tu audiencia es la dirección de "The Core School".

    **TAREA:** Basándote en el análisis completo, define un Plan de Acción Estratégico. Para cada recomendación, sigue el formato SMART (Específica, Medible, Alcanzable, Relevante, con Plazo).

    **DATOS COMPLETOS DEL ANÁLISIS:** {json.dumps(data, indent=2, ensure_ascii=False)}

    **RESPONDE ÚNICAMENTE CON ESTE FORMATO JSON:**
    {{
      "strategic_action_plan": {{
        "title": "Plan de Acción Estratégico",
        "market_outlook": "Basado en las tendencias y el análisis competitivo, ofrece un breve pronóstico del mercado para los próximos 6-12 meses.",
        "strategic_recommendations": [
          {{
            "recommendation": "Capitalizar la Oportunidad Principal: [Describe la acción específica, ej: 'Lanzar campaña de marketing de contenidos sobre el éxito laboral de los alumni en VFX.']",
            "details": "Justifica por qué esta acción aborda la oportunidad más importante detectada en el análisis.",
            "kpis": "Define 1-2 KPIs para medir el éxito. Ej: 'Aumentar el SOV en el tema 'VFX' en 10 puntos; generar un 15% más de leads para programas de VFX.'",
            "timeline": "Define un plazo realista. Ej: 'Próximo trimestre (Q4 2025)." ,
            "priority": "Estima la prioridad. Ej: 'Alta'"
          }},
          {{
            "recommendation": "Mitigar el Riesgo más Crítico: [Describe la acción específica, ej: 'Crear una página de destino sobre transparencia de precios y becas.']",
            "details": "Explica cómo esta acción aborda directamente el riesgo o 'pain point' más urgente encontrado en el análisis.",
            "kpis": "Define 1-2 KPIs. Ej: 'Reducir el sentimiento negativo en el tema 'Precios' en 0.3 puntos; aumentar el tiempo de permanencia en la página de precios en un 30%." ,
            "timeline": "Define un plazo. Ej: 'Próximos 45 días.'",
            "priority": "Estima la prioridad. Ej: 'Crítica'"
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


def get_competitive_analysis_prompt(data):
    """Analista Competitivo: SOV, posicionamiento y debilidades."""
    return f"""
    **ROL:** Eres un Analista de Inteligencia Competitiva. Tu objetivo es analizar el posicionamiento de 'The Core School' frente a sus competidores. Sé directo, analítico y enfócate en insights accionables.

    **DATOS DE MERCADO:** {json.dumps(data, indent=2, ensure_ascii=False)}

    **RESPONDE ÚNICAMENTE CON ESTE FORMATO JSON:**
    {{
      "competitive_landscape": {{
        "title": "Análisis del Panorama Competitivo",
        "overall_positioning": "Describe la posición general de The Core School en el mercado basándote en el ranking de SOV y el sentimiento comparativo. ¿Somos líderes, contendientes, o estamos rezagados?",
        "leader_analysis": "Analiza al competidor líder ('{data.get('kpis', {}).get('sov_leader_name', 'N/A')}'). ¿Cuáles son sus fortalezas clave según los datos de SOV por tema?",
        "competitor_weaknesses": [
            {{
                "competitor": "Nombre del competidor principal (ej. CES)",
                "theme": "El tema específico donde muestran debilidad (sentimiento negativo).",
                "analysis": "Explica por qué esta debilidad es una oportunidad estratégica para nosotros. Conecta el 'pain point' de su audiencia con una fortaleza nuestra."
            }},
            {{
                "competitor": "Nombre de otro competidor relevante",
                "theme": "Otro tema donde muestran debilidad.",
                "analysis": "Describe cómo podemos posicionar nuestro contenido para capturar el interés de la audiencia insatisfecha de este competidor."
            }}
        ]
      }}
    }}
    """

