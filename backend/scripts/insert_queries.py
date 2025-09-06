import psycopg2

# Queries adaptadas a The Core Entertainment Science School
QUERIES = [
    # Indecisión y Motivaciones
    ("¿Cuál es la estimación del número de jóvenes en España (16-25 años) que se declaran indecisos sobre su futuro académico/profesional y qué intereses emergentes en el ámbito del entretenimiento y audiovisual (cine, series, televisión, animación, música, videojuegos, comunicación, marketing digital) destacan en sus conversaciones online?", "The Core School", "Target Audience Research", "es"),
    
    ("¿Qué 'triggers' (eventos, experiencias, referentes culturales, estrenos de cine/series, influencers, festivales) mencionan los jóvenes indecisos en España como detonantes para interesarse por carreras en entretenimiento, cine, videojuegos o música, y qué emociones expresan en esos momentos (curiosidad, esperanza, inseguridad)?", "The Core School", "Motivation Triggers", "es"),
    
    ("¿Cuáles son las motivaciones principales que impulsan a los jóvenes indecisos en España a considerar carreras creativas y de entretenimiento (flexibilidad, pasión, propósito, proyección internacional), y qué factores producen rechazo hacia estudios tradicionales (rigidez, falta de creatividad, estabilidad excesiva)?", "The Core School", "Motivations Analysis", "es"),
    
    ("¿Qué tipos de trabajos o estilos de vida rechazan explícitamente los jóvenes indecisos en España (ej. 'trabajo de oficina', '9 a 5', 'oposiciones'), y qué carreras vinculadas al entretenimiento y audiovisual (realización, guion, producción, animación, diseño de videojuegos, marketing musical) se asocian con mayor sensación de libertad y mejores perspectivas de futuro?", "The Core School", "Career Preferences", "es"),
    
    # Percepción de la Industria
    ("¿Cómo perciben los jóvenes en España la industria del entretenimiento y audiovisual (cine, series, videojuegos, música, streaming, comunicación digital) en términos de prestigio, empleabilidad e innovación, y cómo se asocia la marca The Core School a estas percepciones?", "The Core School", "Industry Perception", "es"),
    
    ("¿Cuáles son las búsquedas y tendencias digitales más frecuentes en España relacionadas con 'carreras creativas', 'profesiones del entretenimiento', 'empleos del futuro' o 'formación en comunicación, videojuegos, música y cine', y cómo pueden vincularse a la propuesta educativa de The Core School?", "The Core School", "Digital Trends", "es"),
    
    # Padres e Influencia
    ("¿Cuáles son las preocupaciones más repetidas por los padres en España cuando sus hijos consideran carreras en el ámbito del entretenimiento y audiovisual (empleabilidad, coste, prestigio, estabilidad), y qué fuentes consultan para informarse sobre instituciones como The Core School?", "The Core School", "Parents Concerns", "es"),
    
    ("¿Qué tipo de argumentos, datos o testimonios resultan más persuasivos para convencer a los padres en España sobre la viabilidad de estudiar en entretenimiento, comunicación o audiovisual (ej. tasas de empleo, casos de éxito en la industria, trayectorias internacionales), y cómo puede The Core School posicionarse en esos mensajes?", "The Core School", "Parent Persuasion", "es"),
    
    # Competencia y Oferta Educativa
    ("¿Qué otras alternativas de formación (FP, grados universitarios, academias de cine, escuelas de música, centros de videojuegos o comunicación digital) aparecen con más frecuencia en el 'set de consideración' de los jóvenes en España frente a The Core School?", "The Core School", "Competitive Analysis", "es"),
    
    ("¿Qué pain points destacan los jóvenes y padres sobre la oferta actual en formación audiovisual/entretenimiento en España (programas largos, costes altos, poca conexión real con la industria, falta de prácticas), y cómo se diferencian frente a la propuesta de The Core School?", "The Core School", "Pain Points Analysis", "es"),
    
    # Marketing y Estrategia
    ("¿Qué canales y plataformas digitales (TikTok, YouTube, Twitch, Instagram, Spotify, foros de videojuegos) son los más efectivos para llegar a jóvenes en España, y qué formatos de contenido (testimonios, casos de éxito, experiencias en rodajes, videojuegos, festivales) generan mayor engagement para instituciones como The Core School?", "The Core School", "Digital Marketing", "es"),
    
    ("¿Cómo evoluciona el 'share of voice' y el sentimiento online de The Core School frente a competidores (ECAM, TAI, U-Tad, CES, CEV) en España, y qué oportunidades de posicionamiento aparecen al vincular su marca con términos como 'empleos creativos', 'futuro del entretenimiento', 'formación audiovisual' o 'videojuegos'?", "The Core School", "Brand Monitoring", "es"),
    
    # --- Ampliación propuesta ---
    
    # Competencia y Benchmarking
    ("¿Qué menciones y percepciones generan otras instituciones españolas de formación en cine, comunicación y videojuegos como ECAM, TAI, U-Tad, CES o CEV en comparación con The Core School, y cómo se valoran sus programas?", "The Core School", "Competitor Benchmark", "es"),
    
    ("¿Cómo evoluciona el 'share of voice' digital en España entre The Core School y sus competidores directos, y qué diferencias existen en sentimiento y engagement de los usuarios?", "The Core School", "Share of Voice", "es"),
    
    # Industria Audiovisual y Entretenimiento
    ("¿Qué temas generan mayor conversación online en España sobre la industria del entretenimiento (series, realities, cine, videojuegos, música, streaming) y qué oportunidades de formación emergen de esas conversaciones?", "The Core School", "Industry Buzz", "es"),
    
    ("¿Qué tendencias emergentes en entretenimiento (IA en guion, producción virtual, animación 3D, gaming competitivo, marketing musical digital) destacan en España y qué implicaciones tienen para la formación?", "The Core School", "Trends Analysis", "es"),
    
    # Empleabilidad y Mercado Laboral
    ("¿Cómo se percibe la empleabilidad de los titulados en carreras de entretenimiento y audiovisual en España en términos de salarios, estabilidad y proyección internacional, y qué casos de éxito se mencionan?", "The Core School", "Employment Outcomes", "es"),
    
    ("¿Qué perfiles del entretenimiento (realizador, productor, diseñador de videojuegos, guionista, animador 3D, músico digital, especialista en marketing audiovisual) tienen mayor demanda en España en 2025?", "The Core School", "Job Market", "es"),
    
    # Reputación de Marca y Alianzas
    ("¿En qué contextos aparece The Core School vinculado a marcas del sector audiovisual y entretenimiento (plataformas de streaming, productoras, discográficas, empresas de gaming), y qué percepción genera?", "The Core School", "Brand Partnerships", "es"),
    
    ("¿Qué impacto tienen las colaboraciones de The Core School con profesionales reconocidos o empresas del sector en su reputación online en España?", "The Core School", "Reputation Drivers", "es"),
    
    # Estudiantes y Comunidad
    ("¿Qué experiencias narran los estudiantes actuales o antiguos de The Core School en redes sociales sobre su paso por la institución (ambiente, prácticas, oportunidades laborales), y qué emociones predominan?", "The Core School", "Student Voice", "es"),
    
    ("¿Qué expectativas expresan los jóvenes en España sobre la experiencia universitaria en carreras creativas (vida en campus, networking, prácticas reales, contactos en la industria), y cómo se vincula esto con The Core School?", "The Core School", "Student Expectations", "es"),
    
    # Innovación y Futuro
    ("¿Cómo se percibe la integración de nuevas tecnologías (IA, VR/AR, producción virtual, música digital) en la formación audiovisual y de entretenimiento en España, y qué oportunidades puede aprovechar The Core School?", "The Core School", "Innovation Perception", "es"),
    
    ("¿Qué discursos circulan online en España sobre 'el futuro del entretenimiento' y 'los empleos creativos del mañana', y cómo puede The Core School conectar su propuesta educativa con esos mensajes?", "The Core School", "Future Outlook", "es")
]

# --- Nuevas queries solicitadas ---
# Fase 1: Descubrimiento y Exploración
QUERIES += [
    ("¿Qué carreras creativas tienen más futuro en España?", "The Core School", "Future Outlook & Trends", "es"),
    ("¿Qué hay que estudiar para trabajar en cine o en series de Netflix?", "The Core School", "Curriculum & Programs", "es"),
    ("Salidas profesionales y sueldos en el sector de los videojuegos.", "The Core School", "Employment & Jobs", "es"),
    ("¿Qué hace un productor de televisión y qué se necesita para serlo?", "The Core School", "Employment & Jobs", "es"),
    ("Trabajos en el mundo audiovisual que no sean los típicos.", "The Core School", "Employment & Jobs", "es"),
    ("¿Se puede vivir bien trabajando en la industria del cine en España?", "The Core School", "Employment & Jobs", "es"),
    ("Historias de éxito de gente que estudió carreras creativas.", "The Core School", "Alumni & Success Stories", "es"),
    ("¿Qué perfiles buscan las productoras de videojuegos y series?", "The Core School", "Job Market", "es"),
    ("¿Merece la pena estudiar una carrera en el sector audiovisual o hay mucho paro?", "The Core School", "Parents & Family Concerns", "es"),
    ("Cómo saber si una carrera creativa es para mí.", "The Core School", "Audience & Research", "es"),
    ("¿Cuánto cuesta estudiar cine en España?", "The Core School", "Scholarships & Cost", "es"),
    ("Becas para estudiar carreras de arte y creatividad en Madrid.", "The Core School", "Scholarships & Cost", "es"),
    ("¿Cuántos jóvenes en España no saben qué estudiar y qué carreras creativas les interesan más?", "The Core School", "Audience & Research", "es"),
    ("¿Qué inspira a los jóvenes a estudiar carreras de cine, TV o videojuegos en lugar de grados tradicionales?", "The Core School", "Motivation & Triggers", "es"),
    ("¿Por qué los jóvenes en España rechazan trabajos de oficina y qué carreras audiovisuales ven como una mejor alternativa?", "The Core School", "Career Preferences", "es"),
]

# Fase 2: Comparando Opciones (Búsqueda de Escuelas)
QUERIES += [
    ("Mejores escuelas para estudiar cine en Madrid.", "The Core School", "Competition & Benchmarking", "es"),
    ("¿Dónde puedo estudiar guion en España?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Qué diferencia hay entre un grado universitario de comunicación audiovisual y una escuela especializada?", "The Core School", "Curriculum & Programs", "es"),
    ("Máster para especializarme en postproducción y efectos visuales.", "The Core School", "Curriculum & Programs", "es"),
    ("Cursos o grados para aprender a crear formatos de TV como concursos o realities.", "The Core School", "Curriculum & Programs", "es"),
    ("Compara The Core School con ECAM, TAI y U-Tad: ¿cuál es mejor para estudiar cine?", "The Core School", "Competition & Benchmarking", "es"),
    ("Ventajas de The Core School frente a otras escuelas de audiovisuales en España.", "The Core School", "Competition & Benchmarking", "es"),
    ("Opiniones sobre el precio de The Core School, ¿vale la pena comparado con otras opciones?", "The Core School", "Scholarships & Cost", "es"),
    ("Mejor escuela en España para estudiar producción de TV y realities.", "The Core School", "Competition & Benchmarking", "es"),
    ("¿De qué escuela de cine se habla más en redes sociales en España: The Core School, ECAM o TAI?", "The Core School", "Share of Voice & Monitoring", "es"),
    ("ECAM vs The Core School para estudiar dirección.", "The Core School", "Competition & Benchmarking", "es"),
    ("TAI vs The Core School, opiniones de alumnos.", "The Core School", "Competition & Benchmarking", "es"),
    ("¿Qué escuela tiene mejores conexiones con la industria, U-Tad o The Core School?", "The Core School", "Brand Partnerships", "es"),
]

# Fase 3: Interés Específico en The Core School
QUERIES += [
    ("¿Qué opinan los estudiantes sobre The Core School?", "The Core School", "Students & Experience", "es"),
    ("¿Qué se dice de The Core School en TikTok y foros en 2025?", "The Core School", "Digital Trends & Marketing", "es"),
    ("¿Es fácil encontrar trabajo después de estudiar en The Core School?", "The Core School", "Employment & Jobs", "es"),
    ("¿Qué sueldo se puede esperar al graduarse en The Core School?", "The Core School", "Employment & Jobs", "es"),
    ("¿Qué tal son los profesores y qué conexiones tiene The Core School con la industria?", "The Core School", "Students & Experience", "es"),
    ("Ejemplos de alumnos de The Core School que ahora trabajen en grandes empresas.", "The Core School", "Alumni & Success Stories", "es"),
    ("¿Cómo son las instalaciones y platós de The Core School?", "The Core School", "Campus & Facilities", "es"),
    ("¿Qué hay que hacer para entrar en The Core School?", "The Core School", "Admissions & Enrollment", "es"),
    ("¿Qué becas y ayudas ofrece The Core School?", "The Core School", "Scholarships & Cost", "es"),
    ("¿Qué asignaturas o másteres hacen única a The Core School?", "The Core School", "Curriculum & Programs", "es"),
    ("¿The Core School enseña a usar IA y nuevas tecnologías para cine y videojuegos?", "The Core School", "Innovation & Technology", "es"),
    ("Casos de éxito de alumni de The Core School.", "The Core School", "Alumni & Success Stories", "es"),
    ("Experiencia de los estudiantes en el campus de The Core School.", "The Core School", "Students & Experience", "es"),
    ("¿Qué empresas colaboran con The Core School para hacer prácticas?", "The Core School", "Brand Partnerships", "es"),
]

# Fase 4: Dudas de Padres y Familiares
QUERIES += [
    ("Cuando un joven quiere estudiar algo audiovisual, ¿qué es lo que más preocupa a los padres en España?", "The Core School", "Parents & Family Concerns", "es"),
    ("¿Qué datos sobre empleo y salarios convencen a los padres de que estudiar una carrera audiovisual es una buena opción?", "The Core School", "Parents & Family Concerns", "es"),
    ("Argumentos para convencer a mis padres de que quiero estudiar cine.", "The Core School", "Parents & Family Concerns", "es"),
    ("Seguridad laboral y estabilidad en el sector audiovisual.", "The Core School", "Parents & Family Concerns", "es"),
    ("Dudas sobre el coste de la matrícula en The Core School.", "The Core School", "Scholarships & Cost", "es"),
    ("¿The Core School es un título oficial o privado?", "The Core School", "Admissions & Enrollment", "es"),
    ("Opiniones de padres sobre The Core School.", "The Core School", "Parents & Family Concerns", "es"),
    ("¿Qué apoyo ofrece The Core School a los estudiantes para encontrar trabajo?", "The Core School", "Employment & Jobs", "es"),
]

def insert_thecore_queries():
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        database="ai_visibility",
        user="postgres",
        password="postgres"
    )
    cur = conn.cursor()

    # BORRAR COMPLETAMENTE todas las queries anteriores
    print("🗑️ Eliminando TODAS las queries anteriores (galletas, etc.)...")
    
    # Primero borrar menciones e insights relacionados (para evitar errores de foreign key)
    cur.execute("DELETE FROM mentions;")
    cur.execute("DELETE FROM insights;")
    # Borrar citations solo si existe
    try:
        cur.execute("DELETE FROM citations;")
    except psycopg2.errors.UndefinedTable:
        conn.rollback()
        print("ℹ️ Tabla 'citations' no existe. Continuando…")
    
    # Ahora borrar todas las queries
    cur.execute("DELETE FROM queries;")
    
    print("✅ Base de datos limpiada completamente.")
    
    # Añadir columna language si no existe
    try:
        cur.execute("ALTER TABLE queries ADD COLUMN language TEXT DEFAULT 'en';")
        conn.commit()
        print("✅ Columna 'language' añadida.")
    except psycopg2.errors.DuplicateColumn:
        conn.rollback()
        print("ℹ️ La columna 'language' ya existía.")

    # Insertar las queries de The Core
    print(f"🎯 Insertando las {len(QUERIES)} queries de The Core School...")
    for i, (query, brand, topic, lang) in enumerate(QUERIES, 1):
        # Evitar duplicados de forma portable (sin ON CONFLICT)
        cur.execute("SELECT 1 FROM queries WHERE query = %s", (query,))
        exists = cur.fetchone() is not None
        if not exists:
            cur.execute(
                """
                INSERT INTO queries (query, brand, topic, language, enabled)
                VALUES (%s, %s, %s, %s, TRUE)
                """,
                (query, brand, topic, lang)
            )
            print(f"   {i:2d}. {query[:80]}... (+)")
        else:
            print(f"   {i:2d}. {query[:80]}... (skip)")

    conn.commit()
    print(f"✅ Insertadas las {len(QUERIES)} queries de The Core School correctamente.\n")

    # Mostrar queries activas
    print("📌 Queries ACTIVAS en la base de datos:")
    cur.execute("""
        SELECT id, brand, topic, LEFT(query, 80) as query_preview 
        FROM queries 
        WHERE enabled = TRUE 
        ORDER BY id DESC;
    """)
    active_queries = cur.fetchall()
    
    for row in active_queries:
        print(f"   ID {row[0]:2d}: [{row[1]}] {row[2]} - {row[3]}...")

    # Verificar conteo total
    cur.execute("SELECT COUNT(*) FROM queries WHERE enabled = TRUE")
    total_active = cur.fetchone()[0]
    print(f"\n📊 Total de queries activas: {total_active}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    print("🚀 CONFIGURANDO QUERIES DE THE CORE SCHOOL")
    print("=" * 60)
    insert_thecore_queries()
    
    print("\n🎬 ¡Listo! Ahora puedes:")
    print("1. Ejecutar el scheduler: python -c \"from src.scheduler.poll import main; main(loop_once=True)\"")
    print("2. Ver el frontend en: http://localhost:3000")
    print("3. Verificar datos: python scripts/show_all.py")