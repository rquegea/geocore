import json


def get_executive_summary_prompt(data):
    """Analista Ejecutivo: KPIs y Resumen Ejecutivo."""
    return f"""
    **ROL:** Eres un Analista Principal en una consultora estratégica de primer nivel (estilo McKinsey/BCG). Tu audiencia es el equipo directivo de "The Core School". Tu lenguaje debe ser conciso, basado en datos y enfocado en el impacto de negocio.
    **TAREA:** Analiza los datos de mercado proporcionados para redactar un Resumen Ejecutivo de alto impacto.
    **DATOS CLAVE:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "executive_summary": {{
        "title": "Informe Ejecutivo de Inteligencia de Mercado y Estrategia",
        "headline": "Genera un titular de una sola frase que resuma el insight más crítico del periodo. Debe ser impactante y directo (ej: 'La percepción de marca se fortalece en áreas de especialización clave, pero la visibilidad general disminuye frente a una competencia agresiva').",
        "key_findings": [
          "Hallazgo #1: Describe la conclusión más importante sobre nuestra visibilidad y reputación, usando datos específicos.",
          "Hallazgo #2: Describe la conclusión más relevante sobre nuestra posición competitiva y Share of Voice, mencionando al competidor principal.",
          "Hallazgo #3: Describe la conclusión principal sobre la percepción de nuestra audiencia (temas positivos vs. negativos) y qué revela esto."
        ],
        "overall_assessment": "Ofrece una evaluación final y concluyente. ¿Hemos ganado o perdido terreno en el mercado durante este periodo y cuáles son las razones fundamentales detrás de este cambio?"
      }}
    }}
    """


def get_market_analysis_prompt(data):
    """Analista de Mercado y Competencia."""
    return f"""
    **ROL:** Eres un Analista de Inteligencia de Mercado. Tu misión es analizar el panorama competitivo y las tendencias generales del sector para The Core School.
    **TAREA:** Analiza el ranking de Share of Voice, los temas asociados a competidores y las tendencias emergentes.
    **DATOS:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "market_analysis": {{
        "title": "Análisis del Mercado y Panorama Competitivo",
        "market_position": "Describe nuestra posición actual en el ranking de SOV. ¿Somos líderes, retadores o un jugador de nicho? ¿Estamos ganando o perdiendo terreno?",
        "competitor_strategies": "Analiza las estrategias de nuestros 2 principales competidores basándote en los temas en los que se enfocan. ¿Están atacando nuestros puntos débiles o compitiendo en nuestras fortalezas?",
        "emerging_trends": "Identifica y describe la tendencia de mercado más significativa detectada en los datos y qué implicaciones tiene para el sector educativo audiovisual."
      }}
    }}
    """


def get_brand_analysis_prompt(data):
    """Analista de Marca y Consumidor."""
    return f"""
    **ROL:** Eres un Analista de Salud de Marca y Voz del Cliente. Tu objetivo es traducir datos de sentimiento y citas textuales en un diagnóstico claro de la percepción de la marca.
    **TAREA:** Analiza los temas positivos/negativos, oportunidades, riesgos y citas para realizar un diagnóstico completo de la marca The Core School.
    **DATOS:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "brand_analysis": {{
        "title": "Análisis de Marca y Comportamiento del Consumidor",
        "brand_strengths": "Basado en los temas con sentimiento más positivo, identifica y describe nuestras 2-3 fortalezas competitivas más claras en la mente del consumidor.",
        "brand_weaknesses": "Basado en los temas con sentimiento más negativo y los riesgos detectados, identifica nuestros 2-3 puntos de dolor más urgentes que necesitan acción inmediata.",
        "voice_of_the_market": "Sintetiza la narrativa que emerge de las citas textuales. ¿Qué historia nos está contando el mercado sobre su experiencia real con nosotros?"
      }}
    }}
    """


def get_recommendations_prompt(data):
    """Estratega y Planificador."""
    return f"""
    **ROL:** Eres un Consultor de Estrategia Senior. Tu trabajo es destilar todo el análisis previo en un plan de acción ejecutivo, priorizado y de alto impacto.
    **TAREA:** Basándote en todo el contexto, define las perspectivas futuras y las recomendaciones estratégicas.
    **DATOS:** {json.dumps(data, indent=2, ensure_ascii=False)}
    **RESPONDE ÚNICAMENTE CON ESTE JSON:**
    {{
      "recommendations": {{
        "title": "Perspectivas y Recomendaciones Estratégicas",
        "market_outlook": "Basado en las tendencias, ofrece un breve pronóstico del mercado para los próximos 6-12 meses.",
        "strategic_levers": [
          {{
            "lever_title": "Capitalizar en la Oportunidad Principal: [Genera un nombre para la oportunidad más importante]",
            "description": "Explica por qué esta es la oportunidad de mayor impacto y cómo se alinea con nuestros objetivos de negocio.",
            "recommended_actions": ["Acción de Marketing/Ventas específica y medible.", "Acción de Producto/Académica a corto plazo.", "Acción de Comunicación/PR para reforzar el posicionamiento."]
          }},
          {{
            "lever_title": "Mitigar el Riesgo más Crítico: [Genera un nombre para el riesgo más urgente]",
            "description": "Describe el riesgo más significativo y su potencial impacto negativo si no se aborda.",
            "recommended_actions": ["Acción inmediata para contener el riesgo (ej. campaña de comunicación).", "Acción a medio plazo para resolver la causa raíz (ej. ajuste de programa)."]
          }}
        ]
      }}
    }}
    """


