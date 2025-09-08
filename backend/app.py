# backend/app.py

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
import os
from datetime import datetime, timedelta
# Importamos una librería más robusta para parsear fechas
from dateutil.parser import parse as parse_date
import json
from dotenv import load_dotenv
import re
import unicodedata
from difflib import SequenceMatcher
from src.engines.openai_engine import fetch_response

load_dotenv()

app = Flask(__name__)
CORS(app)

# --- CONFIGURACIÓN Y HELPERS ---

def _env(*names: str, default: str | int | None = None):
    for n in names:
        v = os.getenv(n)
        if v is not None and v != "":
            return v
    return default

# --- Nueva Función de Categorización con IA ---
def _normalize_text_for_match(text: str) -> list[str]:
    s = (text or "").lower()
    s = unicodedata.normalize("NFKD", s)
    s = re.sub(r"[^a-z0-9áéíóúñü\s]", " ", s)
    tokens = [t for t in s.split() if len(t) >= 2]
    return tokens


def _best_topic_by_similarity(candidate: str, topics: list[str]) -> tuple[str, float]:
    """Devuelve (mejor_topic, score) usando difflib + similitud por tokens."""
    if not topics:
        return candidate, 0.0
    cand_norm = " ".join(_normalize_text_for_match(candidate))
    best = None
    best_score = -1.0
    for t in topics:
        s1 = SequenceMatcher(None, cand_norm, t.lower()).ratio()
        # Jaccard simple de conjuntos de tokens
        a = set(_normalize_text_for_match(candidate))
        b = set(_normalize_text_for_match(t))
        j = (len(a & b) / max(1, len(a | b))) if (a or b) else 0.0
        score = max(s1, j)
        if score > best_score:
            best = t
            best_score = score
    return best or candidate, float(best_score)


def categorize_prompt_with_ai(query_text: str, topics: list[str]) -> str:
    """Usa un LLM para clasificar una query; mapea a categorías existentes si son parecidas."""
    # Preparamos los topics como una lista numerada para la IA
    topics_list_str = "\n".join([f"{i+1}. {topic}" for i, topic in enumerate(topics)])

    prompt = f"""
Eres un asistente experto en organización de contenido para "The Core School". Tu tarea es clasificar la siguiente "Consulta del Usuario" en una de las "Categorías Disponibles".

Instrucciones Clave:

Si la consulta es clara y relevante para la escuela (cine, audiovisual, software, videojuegos, marketing, etc.), clasifícala en una categoría existente o crea una nueva.

Si la consulta es demasiado vaga, ambigua, sin sentido, o completamente irrelevante (ej. "dónde comprar pan", "el cielo es azul"), responde únicamente con la palabra: Inclasificable.

Categorías Disponibles:
{topics_list_str}

Consulta del Usuario:
"{query_text}"

Responde solo con el nombre de la categoría o con la palabra "Inclasificable".
"""
    try:
        # Usamos el motor de OpenAI para obtener la respuesta
        best_category = fetch_response(prompt, model="gpt-4o-mini", temperature=0.0)

        # Limpiamos respuesta (a veces IA añade números o frases)
        cleaned_category = (best_category or "").strip()
        if "\n" in cleaned_category:
            cleaned_category = cleaned_category.split("\n", 1)[0]
        if ":" in cleaned_category and cleaned_category.lower().startswith("categoria"):
            cleaned_category = cleaned_category.split(":", 1)[-1]
        cleaned_category = cleaned_category.strip().split('.')[-1].strip()

        if cleaned_category.lower() == "inclasificable":
            return "Inclasificable"

        # Si coincide exactamente con una categoría conocida
        if cleaned_category in topics:
            return cleaned_category

        # Si no coincide, mapear por similitud a categoría existente cuando sea alta
        mapped, score = _best_topic_by_similarity(cleaned_category, topics)
        if score >= 0.72:
            return mapped

        # Como respaldo: si la query contiene términos del dominio, preferir el mejor match aunque no supere umbral alto
        DOMAIN_HINTS = [
            "cine", "film", "rodaje", "guion", "guión", "fotografia", "fotografía",
            "animacion", "animación", "vfx", "edicion", "edición", "postproduccion", "postproducción",
            "videojuego", "videojuegos", "programacion", "programación", "software", "ingenieria", "ingeniería",
            "marketing", "comunicacion", "comunicación", "master", "máster", "grado", "curso", "beca", "becas",
            "escuela", "universidad"
        ]
        qtoks = set(_normalize_text_for_match(query_text))
        if any(h in qtoks for h in DOMAIN_HINTS) and score >= 0.6:
            return mapped

        # En caso contrario, devolver tal cual (puede ser nueva categoría)
        return cleaned_category or (mapped if mapped else "Inclasificable")

    except Exception as e:
        print(f"Error en la categorización con IA: {e}")
        # Si todo falla, volvemos a la lógica antigua como respaldo
        return categorize_prompt(None, query_text)

DB_CONFIG = {
    # Preferimos variables con prefijo POSTGRES_ (docker compose),
    # si no existen caemos a DB_* y finalmente a un valor por defecto seguro.
    "host": _env("POSTGRES_HOST", "DB_HOST", default="localhost"),
    "port": int(_env("POSTGRES_PORT", "DB_PORT", default=5433)),
    "database": _env("POSTGRES_DB", "DB_NAME", default="ai_visibility"),
    "user": _env("POSTGRES_USER", "DB_USER", default="postgres"),
    "password": _env("POSTGRES_PASSWORD", "DB_PASSWORD", default="postgres"),
}

def get_db_connection():
    try:
        # Debug: mostrar configuración (sin password)
        dbg = {k: ("***" if k == "password" else v) for k, v in DB_CONFIG.items()}
        print(f"DB_CONFIG: {dbg}")
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print(f"ERROR: No se pudo conectar a la base de datos: {e}")
        raise e


# --- Detección de marcas reutilizable ---
BRAND_SYNONYMS = {
    "The Core School": ["the core", "the core school", "thecore"],
    "U-TAD": ["u-tad", "utad"],
    "ECAM": ["ecam"],
    "TAI": ["tai"],
    "CES": ["ces"],
    "CEV": ["cev"],
    "FX Barcelona Film School": ["fx barcelona", "fx barcelona film school", "fx animation"],
    "Septima Ars": ["septima ars", "séptima ars"],
}

def _normalize_list(xs):
    out = []
    if not xs:
        return out
    try:
        for t in xs:
            s = str(t or '').lower().strip()
            if s:
                out.append(s)
    except Exception:
        pass
    return out

def _detect_brands(topics_list, resp_text, title_text, payload):
    found = []
    tlist = _normalize_list(topics_list)
    # key_topics: igualdad o substring
    for canon, alts in BRAND_SYNONYMS.items():
        for a in alts:
            if any(a == t or a in t for t in tlist):
                found.append(canon)
                break
    # payload.brands: igualdad o substring
    try:
        brands_payload = []
        if isinstance(payload, dict):
            brands_payload = _normalize_list((payload.get('brands') or []))
        for canon, alts in BRAND_SYNONYMS.items():
            for a in alts:
                if any(a == b or a in b for b in brands_payload):
                    if canon not in found:
                        found.append(canon)
                    break
    except Exception:
        pass
    # substrings en texto/título
    txt = f"{resp_text or ''} {title_text or ''}"
    for canon, alts in BRAND_SYNONYMS.items():
        if any(a in txt for a in alts):
            if canon not in found:
                found.append(canon)
    return found

def ensure_taxonomy_table():
    """Crea la tabla de taxonomía si no existe."""
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS topic_taxonomy (
            id SERIAL PRIMARY KEY,
            brand TEXT NOT NULL,
            category TEXT NOT NULL,
            keywords JSONB DEFAULT '[]'::jsonb,
            emoji TEXT DEFAULT NULL,
            UNIQUE(brand, category)
        );
        """
    )
    conn.commit(); cur.close(); conn.close()

def get_category_catalog_for_brand(brand: str | None) -> list[str]:
    """Obtiene el catálogo de categorías para una brand desde topic_taxonomy.
    Si no hay filas, devuelve el catálogo por defecto (_CATEGORY_KEYWORDS).
    """
    try:
        ensure_taxonomy_table()
        brand_eff = brand or os.getenv('DEFAULT_BRAND', 'The Core School')
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT category FROM topic_taxonomy WHERE brand = %s", (brand_eff,))
        rows = cur.fetchall(); cur.close(); conn.close()
        return [r[0] for r in rows] if rows else list(_CATEGORY_KEYWORDS.keys())
    except Exception:
        return list(_CATEGORY_KEYWORDS.keys())

def parse_filters(request):
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Da prioridad a las fechas específicas si se proporcionan
    if start_date_str and end_date_str:
        start_date = parse_date(start_date_str)
        # Añadimos un día al end_date para incluir el día completo en la consulta
        end_date = parse_date(end_date_str) + timedelta(days=1) 
    else:
        # Lógica de fallback si no se especifican fechas
        range_param = request.args.get('range', '30d')
        end_date = datetime.now()
        if range_param == '24h': start_date = end_date - timedelta(hours=24)
        elif range_param == '7d': start_date = end_date - timedelta(days=7)
        elif range_param == '90d': start_date = end_date - timedelta(days=90)
        else: start_date = end_date - timedelta(days=30)
    
    model = request.args.get('model', 'all')
    source = request.args.get('source', 'all')
    topic = request.args.get('topic', 'all')
    brand = request.args.get('brand', os.getenv('DEFAULT_BRAND', 'The Core School'))
    sentiment = request.args.get('sentiment', 'all')
    hide_bots = request.args.get('hideBots', '0') == '1'
    status_param = request.args.get('status', 'active')
    
    print(f"DEBUG: Filtrando desde {start_date} hasta {end_date}") # Para depuración
    
    return {
        'start_date': start_date,
        'end_date': end_date,
        'model': model,
        'source': source,
        'topic': topic,
        'brand': brand,
        'sentiment': sentiment,
        'hide_bots': hide_bots,
        'status': status_param,
    }


# --- Normalización y agrupación de Topics ---

def _strip_accents(text: str) -> str:
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])


def _normalize_topic_key(text: str) -> str:
    txt = _strip_accents((text or '').strip().lower())
    txt = re.sub(r"[\-_]+", " ", txt)
    txt = re.sub(r"[^a-z0-9\s]+", "", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


_TOPIC_SYNONYMS = {
    # canonical_key: list of alternative keys
    "target audience research": ["audience research", "research audience", "research target audience"],
    "motivation triggers": ["motivation trigger", "triggers", "motivational triggers"],
    "motivations": ["motivations analysis", "motivation analysis"],
    "digital trends": ["trends digital", "online trends"],
    "industry perception": ["perception industry", "brand perception"],
    "competitive analysis": ["competitor analysis", "competition analysis"],
    "competitor benchmark": ["competitor benchmarking", "benchmark competitors"],
    "brand monitoring": ["monitoring brand"],
    "share of voice": ["sov", "voice share"],
    "industry buzz": ["buzz industry"],
    "trends analysis": ["trends", "trend analysis"],
    "employment outcomes": ["employability", "employment"],
    "job market": ["labour market", "labor market"],
    "brand partnerships": ["partnerships", "partnerships brand"],
    "reputation drivers": ["drivers reputation"],
    "student voice": ["students voice"],
    "student expectations": ["expectations students", "students expectations"],
    "innovation perception": ["perception innovation"],
    "future outlook": ["outlook future"],
}


def canonicalize_topic(topic: str) -> str:
    """Devuelve un nombre de topic canónico y legible para agrupar variantes similares."""
    key = _normalize_topic_key(topic or '')
    if not key:
        return 'Uncategorized'

    # Exact matches from synonyms
    for canonical, alts in _TOPIC_SYNONYMS.items():
        if key == canonical:
            return canonical.title()
        if key in alts:
            return canonical.title()

    # Fuzzy match against canonical names
    best_name = None
    best_score = 0.0
    for canonical in list(_TOPIC_SYNONYMS.keys()):
        score = SequenceMatcher(None, key, canonical).ratio()
        if score > best_score:
            best_score = score
            best_name = canonical
    if best_score >= 0.88 and best_name:
        return best_name.title()

    # Fallback: Title Case of cleaned text
    return ' '.join(w.capitalize() for w in key.split()) or 'Uncategorized'


# Nueva función: agrupar topics con IA en categorías estratégicas
def group_topics_with_ai(topics_rows: list[dict]) -> list[dict]:
    try:
        topics_list_str = "\n".join([f"- {t.get('topic','')} | count={t.get('count',0)} | avg_sentiment={t.get('avg_sentiment',0.0):.2f}" for t in topics_rows])
        
        # --- INICIO DE LA MODIFICACIÓN ---
        # El nuevo prompt con categorías más granulares y mejores instrucciones
        prompt = f"""
Eres un analista de inteligencia de mercado para "The Core School". Tu misión es agrupar una lista de temas en las siguientes categorías estratégicas predefinidas. Sé muy estricto y preciso.

**Categorías Predefinidas (USA SOLO ESTAS):**
- **Menciones de Marca Propia:** Exclusivamente para temas que se refieren a "The Core School".
- **Menciones de Competidores Directos:** Para otras escuelas de cine y audiovisual (ej. U-tad, ECAM, TAI, ESCAC).
- **Menciones de Universidades Tradicionales:** Para universidades generalistas que ofrecen grados relacionados (ej. Complutense, Rey Juan Carlos).
- **Programas y Grados:** Temas sobre áreas de estudio específicas (ej. "dirección de cine", "ingeniería de software", "comunicación audiovisual").
- **Becas y Admisiones:** Temas sobre el proceso de entrada y costes (ej. "becas", "precio", "admisiones").
- **Salidas Profesionales:** Temas relacionados con el empleo post-graduación (ej. "salidas laborales", "empleabilidad").
- **Temas Generales del Sector:** Conversaciones amplias sobre la industria (ej. "sector audiovisual", "tendencias cine").

**Instrucciones:**
1.  Asigna CADA tema de la lista a una de las 7 categorías.
2.  Si un tema no encaja claramente, asígnalo a "Temas Generales del Sector".
3.  Calcula el sentimiento medio y las ocurrencias totales para cada categoría.
4.  Devuelve el resultado ÚNICAMENTE en formato JSON, sin texto adicional.

**Formato de Salida JSON Esperado:**
```json
[
  {{
    "group_name": "Menciones de Competidores Directos",
    "avg_sentiment": 0.65,
    "total_occurrences": 15,
    "topics": [
      {{ "topic": "u-tad", "count": 8, "avg_sentiment": 0.7 }},
      {{ "topic": "ecam", "count": 7, "avg_sentiment": 0.5 }}
    ]
  }}
]
```
Lista de Temas a Analizar:
{topics_list_str}
"""
# --- FIN DE LA MODIFICACIÓN ---

        raw = fetch_response(prompt, model="gpt-4o-mini", temperature=0.0)
        
        # Extraer el bloque JSON de la respuesta
        import re as _re
        match = _re.search(r"\[\s*\{[\s\S]*\}\s*\]", raw)
        if match:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return data
        return []
    except Exception:
        # En caso de error, devuelve una estructura vacía para no romper el frontend.
        return []

# Categorías temáticas para agrupar prompts similares (ES/EN)
_CATEGORY_KEYWORDS = {
    "Audience & Research": [
        "audience", "público", "publico", "target", "investigacion", "investigación", "research"
    ],
    "Motivation & Triggers": [
        "motivacion", "motivación", "motivation", "trigger", "triggers", "detonante", "inspiracion", "inspiración"
    ],
    "Parents & Family Concerns": [
        "padres", "familia", "parents", "preocupaciones", "concerns", "temores"
    ],
    "Competition & Benchmarking": [
        "competencia", "competidores", "competitor", "benchmark", "comparacion", "comparación", "competitive"
    ],
    "Brand & Reputation": [
        "marca", "brand", "reputacion", "reputación", "monitoring", "percepcion", "percepción"
    ],
    "Digital Trends & Marketing": [
        "tendencias", "trends", "search", "busquedas", "búsquedas", "marketing", "digital", "social", "plataformas"
    ],
    "Industry & Market": [
        "industria", "industry", "mercado", "market", "buzz"
    ],
    "Students & Experience": [
        "estudiantes", "students", "alumnos", "experiencia", "expectativas", "voice"
    ],
    "Innovation & Technology": [
        "innovacion", "innovación", "ia", "ai", "vr", "ar", "tecnologia", "tecnología", "produccion virtual", "virtual"
    ],
    "Employment & Jobs": [
        "empleabilidad", "empleo", "empleos", "trabajos", "jobs", "salarios", "job market", "outcomes"
    ],
    "Share of Voice & Monitoring": [
        "share of voice", "sov", "voz", "monitoring"
    ],
    "Future Outlook & Trends": [
        "futuro", "future", "outlook"
    ],
    "Partnerships & Collaborations": [
        "colaboraciones", "partnerships", "partners", "alianzas"
    ],
    # Nuevas categorías
    "Admissions & Enrollment": [
        "admisiones", "admission", "inscripcion", "inscripción", "matricula", "matrícula", "proceso", "requisitos",
        "plazos", "solicitud"
    ],
    "Scholarships & Cost": [
        "becas", "beca", "coste", "costo", "precio", "prices", "financiacion", "financiación", "roi", "retorno"
    ],
    "Curriculum & Programs": [
        "curriculo", "currículo", "curriculum", "plan de estudios", "programas", "asignaturas", "grados", "fp",
        "masters", "másteres", "itinerarios"
    ],
    "Alumni & Success Stories": [
        "alumni", "egresados", "casos de exito", "casos de éxito", "testimonios", "trayectorias", "salidas"
    ],
    "Campus & Facilities": [
        "campus", "instalaciones", "equipamiento", "platós", "estudios", "laboratorios", "recursos"
    ],
    "Events & Community": [
        "eventos", "open day", "jornadas", "ferias", "festival", "comunidad", "networking", "meetup"
    ],
    # Nuevo: categoría específica para comunicación audiovisual y media
    "Audiovisual & Media": [
        "comunicacion audiovisual", "comunicación audiovisual", "audiovisual", "cine", "rodaje",
        "montaje", "postproduccion", "postproducción", "sonido", "vfx", "fx", "efectos visuales",
        "animacion", "animación", "guion", "guión", "fotografia", "fotografía", "produccion",
        "producción", "realizacion", "realización", "edicion", "edición"
    ],
    # Más tecnología/ingeniería para evitar solapamientos genéricos
    "Innovation & Technology": [
        "innovacion", "innovación", "tecnologia", "tecnología", "ia", "ai", "vr", "ar",
        "realidad virtual", "realidad aumentada", "machine learning", "big data", "iot", "ciencia de datos",
        "transformacion digital", "transformación digital"
    ],
    # Categoría específica si se desea separar de Innovación
    "Engineering & Software": [
        "ingenieria de software", "ingeniería de software", "desarrollo de software",
        "programacion", "programación", "programacion de videojuegos", "desarrollo backend",
        "desarrollo frontend", "devops", "arquitectura de software", "sistemas distribuidos",
        "bases de datos", "algoritmos", "computer science"
    ],
}


def _tokenize(text: str) -> set:
    t = _normalize_topic_key(text)
    return set(re.findall(r"[a-z0-9]+", t))


def categorize_prompt(topic: str | None, query_text: str | None) -> str:
    """Asigna categoría usando la versión detallada (reglas + scoring)."""
    try:
        detailed = categorize_prompt_detailed(topic, query_text)
        return detailed.get("category") or canonicalize_topic(topic or '')
    except Exception:
        return canonicalize_topic(topic or '')


def categorize_prompt_detailed(topic: str | None, query_text: str | None) -> dict:
    """Versión detallada: devuelve categoría, puntuación, alternativas y sugerencia.
    Regla: combina keywords de taxonomía, similitud con nombre de categoría y patrones de frases.
    """
    brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')

    # 1) Cargar taxonomía/keywords
    try:
        ensure_taxonomy_table()
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT category, COALESCE(keywords,'[]'::jsonb) FROM topic_taxonomy WHERE brand = %s", (brand,))
        rows = cur.fetchall(); cur.close(); conn.close()
        categories_source = { r[0]: list(r[1] or []) } if rows else _CATEGORY_KEYWORDS
        if rows:
            # Si solo hay una fila, ampliar con base por defecto
            categories_source = { r[0]: list(r[1] or []) for r in rows }
    except Exception:
        categories_source = _CATEGORY_KEYWORDS

    full_text = (topic or '') + ' ' + (query_text or '')
    tokens = _tokenize(full_text)

    # 2) Patrones complementarios (ES/EN)
    PATTERNS = [
        (r"alumni|casos\s+de\s+exito|éxito|testimonios|trayectorias", "Alumni & Success Stories"),
        # Programas: consultas de intención de estudio y centros de formación
        (r"(d[oó]nde\s+estudiar|centros?\s+de\s+formaci[oó]n|grado\s+en|grados?\s+de|m[aá]ster(?:es)?\s+en)", "Curriculum & Programs"),
        (r"plan\s+de\s+estudios|curriculum|asignaturas|programas", "Curriculum & Programs"),
        (r"empleo|empleabilidad|salidas|profesiones|trabajo|job\s*market", "Employment & Jobs"),
        (r"becas|precio|coste|costo|financiaci[oó]n|roi", "Scholarships & Cost"),
        # Benchmarking: comparativas explícitas tipo "mejor universidad/centro/escuela" o "X vs Y"
        (r"(mejor\s+(universidad|centro|escuela)|\bvs\b|comparar|comparaci[oó]n)", "Competition & Benchmarking"),
        (r"competencia|competidores|benchmark", "Competition & Benchmarking"),
        (r"marca|reputaci[oó]n|monitor", "Brand & Reputation"),
        (r"tendencias|digital|marketing|redes", "Digital Trends & Marketing"),
        (r"campus|instalaciones|recursos", "Campus & Facilities"),
        (r"innovaci[oó]n|tecnolog[ií]a|ia|ai|vr|ar|programaci[oó]n|software|ingenier[íi]a", "Engineering & Software"),
        (r"estudiantes|experiencia|expectativas", "Students & Experience"),
        (r"padres|familia|preocupaciones", "Parents & Family Concerns"),
        (r"comunicaci[oó]n\s+audivisual|comunicaci[oó]n\s+aud[ií]visual|cine|rodaje|montaje|postproducci[oó]n|sonido|vfx|animaci[oó]n|gu[ií]on|fotograf[ií]a|realizaci[oó]n|edici[oó]n", "Audiovisual & Media"),
    ]

    import re
    bonus_pattern: dict[str, int] = {}
    q = full_text.lower()
    for rx, cat in PATTERNS:
        if re.search(rx, q):
            # Los patrones tienen prioridad fuerte
            bonus_pattern[cat] = bonus_pattern.get(cat, 0) + 5

    # Desambiguación temprana entre Audiovisual & Media y Engineering & Software
    audiovisual_terms = [
        "comunicacion audiovisual", "comunicación audiovisual", "cine", "rodaje", "montaje", "postproduccion",
        "postproducción", "sonido", "vfx", "animacion", "animación", "guion", "guión", "fotografia",
        "fotografía", "produccion", "producción", "realizacion", "realización", "edicion", "edición"
    ]
    software_terms = [
        "ingenieria", "ingeniería", "software", "programacion", "programación", "desarrollo", "backend",
        "frontend", "devops", "algoritmos", "bases de datos", "sistemas", "arquitectura"
    ]
    aud_hits = sum(1 for t in audiovisual_terms if t in q)
    soft_hits = sum(1 for t in software_terms if t in q)
    if aud_hits >= soft_hits + 2 and aud_hits >= 2:
        return {
            "category": "Audiovisual & Media",
            "confidence": 0.85,
            "alternatives": [{"category": "Engineering & Software", "score": 0.5}],
            "suggestion": None,
            "suggestion_is_new": False,
            "closest_existing": "Audiovisual & Media",
            "closest_score": 0.9,
            "is_close_match": True,
        }
    if soft_hits >= aud_hits + 2 and soft_hits >= 2:
        return {
            "category": "Engineering & Software",
            "confidence": 0.85,
            "alternatives": [{"category": "Audiovisual & Media", "score": 0.5}],
            "suggestion": None,
            "suggestion_is_new": False,
            "closest_existing": "Engineering & Software",
            "closest_score": 0.9,
            "is_close_match": True,
        }

    # 3) Scoring por categoría
    from difflib import SequenceMatcher
    scores: list[tuple[str, float]] = []
    for cat, kw_list in categories_source.items():
        score = 0.0
        # coincidencia de keywords
        for kw in kw_list:
            kwt = _tokenize(kw)
            if kwt & tokens:
                score += 2.0
        # similitud fuzzy con nombre
        score += SequenceMatcher(None, _normalize_topic_key(' '.join(tokens)), _normalize_topic_key(cat)).ratio() * 1.5
        # bonus por patrones
        score += bonus_pattern.get(cat, 0)
        scores.append((cat, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    best_cat, best_score = (scores[0] if scores else (canonicalize_topic(topic or ''), 0.0))
    second_score = scores[1][1] if len(scores) > 1 else 0.0
    confidence = 0.0
    if best_score > 0:
        # normalización simple en función de separación y magnitud
        confidence = min(1.0, max(0.0, (best_score - second_score + 1) / (best_score + 1)))

    suggestion = None
    suggestion_is_new = False
    # similitud a categorías existentes a partir del texto del prompt
    base_text = canonicalize_topic(query_text or topic or '')
    known = list(categories_source.keys())
    closest_existing = None
    closest_score = 0.0
    for cat in known:
        s = SequenceMatcher(None, _normalize_topic_key(base_text), _normalize_topic_key(cat)).ratio()
        if s > closest_score:
            closest_score = s; closest_existing = cat
    is_close_match = bool(closest_existing and closest_score >= 0.75)
    # Si la confianza es baja o no hay patrones claros, sugerir crear tópico a partir de frase clave
    if confidence < 0.5:
        # heurística: Usa primera coincidencia de PATTERNS como etiqueta si no está ya
        sug = None
        for _, cat in PATTERNS:
            if bonus_pattern.get(cat):
                sug = cat
                break
        if not sug:
            # fallback: usa canónico del topic/consulta
            sug = canonicalize_topic(topic or query_text or 'Uncategorized')
        # si hay un existente muy similar, preferirlo
        if is_close_match:
            suggestion = closest_existing
            suggestion_is_new = False
        else:
            suggestion_is_new = sug not in set(known)
            suggestion = sug

    return {
        "category": best_cat,
        "confidence": round(float(confidence), 2),
        "alternatives": [{"category": c, "score": round(float(s), 2)} for c, s in scores[:5]],
        "suggestion": suggestion,
        "suggestion_is_new": suggestion_is_new,
        "closest_existing": closest_existing,
        "closest_score": round(float(closest_score), 2),
        "is_close_match": is_close_match,
    }


# --- ENDPOINTS DE LA API ---
@app.route('/api/taxonomy', methods=['GET'])
def list_taxonomy():
    try:
        brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
        ensure_taxonomy_table()
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT id, category, COALESCE(keywords,'[]'::jsonb), COALESCE(emoji,'') FROM topic_taxonomy WHERE brand = %s ORDER BY category", (brand,))
        rows = cur.fetchall(); cur.close(); conn.close()
        items = [{"id": r[0], "category": r[1], "keywords": r[2] or [], "emoji": r[3] or None} for r in rows]
        return jsonify({"brand": brand, "items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/taxonomy', methods=['POST'])
def create_taxonomy_item():
    try:
        payload = request.get_json(silent=True) or {}
        brand = payload.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
        category = payload.get('category'); keywords = payload.get('keywords', []); emoji = payload.get('emoji')
        if not category:
            return jsonify({"error": "category is required"}), 400
        ensure_taxonomy_table()
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("INSERT INTO topic_taxonomy (brand, category, keywords, emoji) VALUES (%s,%s,%s,%s) RETURNING id", (brand, category, json.dumps(keywords), emoji))
        new_id = cur.fetchone()[0]; conn.commit(); cur.close(); conn.close()
        return jsonify({"id": new_id, "brand": brand, "category": category, "keywords": keywords, "emoji": emoji}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/taxonomy/<int:item_id>', methods=['PATCH'])
def update_taxonomy_item(item_id: int):
    try:
        payload = request.get_json(silent=True) or {}
        fields = []; values = []
        if 'category' in payload: fields.append('category = %s'); values.append(payload['category'])
        if 'keywords' in payload: fields.append('keywords = %s'); values.append(json.dumps(payload['keywords']))
        if 'emoji' in payload: fields.append('emoji = %s'); values.append(payload['emoji'])
        if not fields:
            return jsonify({"error": "no fields to update"}), 400
        sql = f"UPDATE topic_taxonomy SET {', '.join(fields)} WHERE id = %s RETURNING id, brand, category, keywords, emoji"
        conn = get_db_connection(); cur = conn.cursor(); cur.execute(sql, tuple(values + [item_id]))
        row = cur.fetchone(); conn.commit(); cur.close(); conn.close()
        if not row:
            return jsonify({"error": "not found"}), 404
        return jsonify({"id": row[0], "brand": row[1], "category": row[2], "keywords": row[3], "emoji": row[4]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/taxonomy/<int:item_id>', methods=['DELETE'])
def delete_taxonomy_item(item_id: int):
    try:
        conn = get_db_connection(); cur = conn.cursor(); cur.execute("DELETE FROM topic_taxonomy WHERE id = %s", (item_id,))
        deleted = cur.rowcount; conn.commit(); cur.close(); conn.close()
        if deleted == 0:
            return jsonify({"error": "not found"}), 404
        return jsonify({"message": f"taxonomy item {item_id} deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    try:
        ensure_taxonomy_table()
        conn = get_db_connection()
        conn.close()
        safe_cfg = {k: ("***" if k == "password" else v) for k, v in DB_CONFIG.items()}
        return jsonify({"status": "healthy", "db": safe_cfg})
    except Exception as e:
        safe_cfg = {k: ("***" if k == "password" else v) for k, v in DB_CONFIG.items()}
        return jsonify({"status": "unhealthy", "error": str(e), "db": safe_cfg}), 500

@app.route('/api/mentions', methods=['GET'])
def get_mentions():
    """Obtener menciones con todos los campos enriquecidos."""
    try:
        filters = parse_filters(request)
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Usamos '<' en la fecha final para ser precisos
        # Construcción dinámica de filtros
        where_clauses = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where_clauses.append("m.engine = %s")
            params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where_clauses.append("m.source = %s")
            params.append(filters['source'])
        if filters.get('topic') and filters['topic'] != 'all':
            where_clauses.append("q.topic = %s")
            params.append(filters['topic'])
        # status filter (default active)
        if filters.get('status') and filters['status'] != 'all':
            where_clauses.append("COALESCE(m.status, 'active') = %s")
            params.append(filters['status'])
        # hide bots
        if filters.get('hide_bots'):
            where_clauses.append("COALESCE(m.is_bot, FALSE) = FALSE")

        where_sql = " AND ".join(where_clauses)

        base_query = f"""
        SELECT 
            m.id, m.engine, m.source, m.response, m.sentiment, m.emotion,
            m.confidence_score, m.source_title, m.source_url, m.language,
            m.created_at, q.query as query_text,
            m.summary, m.key_topics, m.generated_insight_id
        FROM mentions m
        JOIN queries q ON m.query_id = q.id
        WHERE {where_sql}
        ORDER BY m.created_at DESC LIMIT %s OFFSET %s
        """
        cur.execute(base_query, params + [limit, offset])
        rows = cur.fetchall()
        
        mentions = []
        for row in rows:
            mentions.append({
                "id": row[0], "engine": row[1], "source": row[2],
                "response": row[3], "sentiment": float(row[4] or 0.0),
                "emotion": row[5] or "neutral",
                "confidence_score": float(row[6] or 0.0),
                "source_title": row[7], "source_url": row[8],
                "language": row[9] or "unknown",
                "created_at": row[10].isoformat() if row[10] else None,
                "query": row[11],
                "summary": row[12],
                "key_topics": row[13] or [],
                "generated_insight_id": row[14]
            })

        count_query = f"""
        SELECT COUNT(*)
        FROM mentions m
        JOIN queries q ON m.query_id = q.id
        WHERE {where_sql}
        """
        cur.execute(count_query, params)
        total = cur.fetchone()[0] or 0
        
        cur.close()
        conn.close()
        
        return jsonify({ "mentions": mentions, "pagination": { "total": total, "limit": limit, "offset": offset, "has_next": offset + limit < total } })
    except Exception as e:
        print(f"Error en get_mentions: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/visibility', methods=['GET'])
def get_visibility():
    """Visibilidad = menciones de la marca / total de menciones (con filtros aplicados).
    Devuelve score del periodo, delta y serie diaria en porcentaje (0–100%).
    """
    try:
        filters = parse_filters(request)
        brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
        conn = get_db_connection(); cur = conn.cursor()

        where = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where.append("m.source = %s"); params.append(filters['source'])
        # Filtro por tema con categorización dinámica por IA (alineado con /api/prompts)
        if filters.get('topic') and filters['topic'] != 'all':
            topic_filter = filters['topic']
            # 1) Obtener catálogo de categorías (taxonomía o por defecto) y todas las queries activas
            available_topics = get_category_catalog_for_brand(filters.get('brand'))
            cur.execute("SELECT id, query FROM queries WHERE enabled = TRUE")
            qrows = cur.fetchall()
            # 2) Categorizar con IA cada query y quedarnos con las del tema seleccionado
            dyn_ids = []
            for qid, qtext in qrows:
                try:
                    cat = categorize_prompt_with_ai(qtext, available_topics)
                except Exception:
                    # Respaldo a la heurística clásica si fallase la IA
                    cat = categorize_prompt(None, qtext)
                if cat == topic_filter:
                    dyn_ids.append(qid)
            if not dyn_ids:
                # No hay queries que caigan en ese tema -> retornar vacío rápido
                return jsonify({"visibility_score": 0.0, "delta": 0.0, "series": []})
            where.append("q.id = ANY(%s)"); params.append(dyn_ids)
        where_sql = " AND ".join(where)

        # Sinónimos/cadenas para detectar la marca en contenido (key_topics o texto)
        BRAND_SYNONYMS = {
            "The Core School": ["the core school", "the core", "thecore"],
        }
        synonyms = [s.lower() for s in BRAND_SYNONYMS.get(brand, [brand.lower()])]
        like_patterns = [f"%{s}%" for s in synonyms]

        # Conteo total por día (denominador)
        cur.execute(f"""
            SELECT DATE(m.created_at) AS d, COUNT(*)
            FROM mentions m
            JOIN queries q ON m.query_id = q.id
            WHERE {where_sql}
            GROUP BY DATE(m.created_at)
            ORDER BY DATE(m.created_at)
        """, tuple(params))
        total_rows = cur.fetchall()

        # Conteo de días donde aparece la marca en el contenido (numerador)
        cur.execute(f"""
            SELECT DATE(m.created_at) AS d, COUNT(*)
            FROM mentions m
            JOIN queries q ON m.query_id = q.id
            WHERE {where_sql}
              AND (
                EXISTS (
                  SELECT 1 FROM jsonb_array_elements_text(COALESCE(to_jsonb(m.key_topics),'[]'::jsonb)) kt
                  WHERE LOWER(TRIM(kt)) = ANY(%s)
                )
                OR LOWER(COALESCE(m.response,'')) LIKE ANY(%s)
                OR LOWER(COALESCE(m.source_title,'')) LIKE ANY(%s)
              )
            GROUP BY DATE(m.created_at)
            ORDER BY DATE(m.created_at)
        """, tuple(params + [synonyms, like_patterns, like_patterns]))
        core_rows = cur.fetchall()

        from datetime import timedelta
        core_by_day = {d: int(c or 0) for d, c in core_rows}
        total_by_day = {d: int(c or 0) for d, c in total_rows}

        start_day = filters['start_date'].date()
        end_day = filters['end_date'].date()
        day = start_day
        series = []
        num_sum = 0
        den_sum = 0
        while day <= end_day:
            num = int(core_by_day.get(day, 0))
            den = int(total_by_day.get(day, 0))
            num_sum += num
            den_sum += den
            pct = round((num / max(den, 1)) * 100.0, 1)
            series.append({"date": day.strftime('%b %d'), "value": pct})
            day += timedelta(days=1)

        visibility_score = round((num_sum / max(den_sum, 1)) * 100.0, 1)

        n = len(series)
        if n >= 2:
            mid = n // 2
            first = sum(p['value'] for p in series[:mid]) / max(mid, 1)
            second = sum(p['value'] for p in series[mid:]) / max(n - mid, 1)
            delta = round(second - first, 1)
        else:
            delta = 0.0

        cur.close(); conn.close()
        return jsonify({"visibility_score": visibility_score, "delta": delta, "series": series})
    except Exception as e:
        print(f"Error en get_visibility: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/visibility/ranking', methods=['GET'])
def get_visibility_ranking():
    """Ranking de visibilidad por marca.
    Para cada marca detectada en respuestas (menciones), calcula
    porcentaje = (# de respuestas en las que aparece la marca) / (total de respuestas)
    con los filtros aplicados (fecha, modelo, source, topic). No filtra por brand
    para que funcione con cualquier cliente/competencia.
    """
    try:
        filters = parse_filters(request)
        conn = get_db_connection(); cur = conn.cursor()

        where = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where.append("m.source = %s"); params.append(filters['source'])
        # Filtro por tema con categorización dinámica por IA (alineado con /api/prompts)
        if filters.get('topic') and filters['topic'] != 'all':
            topic_filter = filters['topic']
            available_topics = get_category_catalog_for_brand(filters.get('brand'))
            cur.execute("SELECT id, query FROM queries WHERE enabled = TRUE")
            qrows = cur.fetchall()
            dyn_ids = []
            for qid, qtext in qrows:
                try:
                    cat = categorize_prompt_with_ai(qtext, available_topics)
                except Exception:
                    cat = categorize_prompt(None, qtext)
                if cat == topic_filter:
                    dyn_ids.append(qid)
            if not dyn_ids:
                return jsonify({"ranking": [], "total_responses": 0})
            where.append("q.id = ANY(%s)"); params.append(dyn_ids)
        where_sql = " AND ".join(where)

        # Traer campos necesarios para detectar marcas (con filtros y tema dinámico ya aplicados)
        cur.execute(f"""
            SELECT m.id, m.key_topics, LOWER(COALESCE(m.response,'')) AS resp, LOWER(COALESCE(m.source_title,'')) AS title,
                   q.topic, i.payload
            FROM mentions m
            JOIN queries q ON m.query_id = q.id
            LEFT JOIN insights i ON i.id = m.generated_insight_id
            WHERE {where_sql}
        """, tuple(params))
        rows = cur.fetchall()

        # Denominador: total de respuestas del CONJUNTO FILTRADO (tema incluido)
        total_responses = len(rows)

        # Diccionario de marcas y sinónimos (genérico para cualquier cliente)
        BRAND_SYNONYMS = {
            "The Core School": ["the core", "the core school", "thecore"],
            "U-TAD": ["u-tad", "utad"],
            "ECAM": ["ecam"],
            "TAI": ["tai"],
            "CES": ["ces"],
            "CEV": ["cev"],
            "FX Barcelona Film School": ["fx barcelona", "fx barcelona film school", "fx animation"],
            "Septima Ars": ["septima ars", "séptima ars"],
        }

        def detect_brands(topics_list, resp_text, title_text, payload):
            found = []
            tlist = [str(t or '').lower().strip() for t in (topics_list or [])]
            # key_topics: igualdad o substring
            for canon, alts in BRAND_SYNONYMS.items():
                for a in alts:
                    if any(a == t or a in t for t in tlist):
                        found.append(canon)
                        break
            # payload.brands: igualdad o substring
            try:
                brands_payload = []
                if isinstance(payload, dict):
                    brands_payload = payload.get('brands') or []
                for canon, alts in BRAND_SYNONYMS.items():
                    for a in alts:
                        if any(a == str(b or '').lower().strip() or a in str(b or '').lower().strip() for b in brands_payload):
                            if canon not in found:
                                found.append(canon)
                            break
            except Exception:
                pass
            # substrings en texto/título
            for canon, alts in BRAND_SYNONYMS.items():
                if any(a in (resp_text or '') or a in (title_text or '') for a in alts):
                    if canon not in found:
                        found.append(canon)
            return found

        # Construir estructura de menciones normalizada
        def normalize_list(xs):
            out = []
            if not xs:
                return out
            try:
                for t in xs:
                    s = str(t or '').lower().strip()
                    if s:
                        out.append(s)
            except Exception:
                pass
            return out

        mentions = []
        for m_id, key_topics, resp_text, title_text, _topic, payload in rows:
            topics_norm = normalize_list(key_topics)
            payload_brands = []
            try:
                if isinstance(payload, dict):
                    payload_brands = normalize_list(payload.get('brands') or [])
            except Exception:
                payload_brands = []
            combined_text = f"{resp_text or ''} {title_text or ''}"
            mentions.append({
                "id": m_id,
                "topics": topics_norm,
                "pbrands": payload_brands,
                "text": str(combined_text).lower(),
            })

        # Contar, para cada competidor, en cuántas respuestas aparece
        counts = {brand: 0 for brand in BRAND_SYNONYMS.keys()}
        for m in mentions:
            for brand, alts in BRAND_SYNONYMS.items():
                found = False
                # key_topics (igualdad o substring)
                for a in alts:
                    if any(a == t or a in t for t in m["topics"]):
                        found = True; break
                # payload.brands
                if not found:
                    for a in alts:
                        if any(a == t or a in t for t in m["pbrands"]):
                            found = True; break
                # texto/título
                if not found:
                    for a in alts:
                        if a in m["text"]:
                            found = True; break
                if found:
                    counts[brand] += 1

        colors = ["bg-blue-500", "bg-red-500", "bg-blue-600", "bg-yellow-500", "bg-gray-800"]
        ranking = []
        denom = max(total_responses, 1)  # SIEMPRE total global de respuestas
        pairs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
        for i, (b, count) in enumerate(pairs):
            pct = (count / denom) * 100.0
            ranking.append({
                "rank": i + 1,
                "name": b,
                "score": f"{pct:.1f}%",
                "change": "+0.0%",
                "positive": True,
                "color": colors[i % len(colors)],
                "selected": False,
            })

        cur.close(); conn.close()
        return jsonify({"ranking": ranking, "total_responses": total_responses})
    except Exception as e:
        print(f"Error en get_visibility_ranking: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/industry/ranking', methods=['GET'])
def get_industry_ranking():
    """Share of Voice general y por tema basado en detección por key_topics.
    - overall_ranking: porcentaje por marca sobre el total de ocurrencias de marcas detectadas
    - by_topic: mismo cálculo pero segmentado por q.topic
    Filtros: mismos de parse_filters (fecha, modelo, source, topic)
    """
    try:
        filters = parse_filters(request)
        conn = get_db_connection(); cur = conn.cursor()

        where = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where.append("m.source = %s"); params.append(filters['source'])
        # Filtro por tema con categorización dinámica por IA (alineado con /api/prompts)
        if filters.get('topic') and filters['topic'] != 'all':
            topic_filter = filters['topic']
            # Obtener catálogo de categorías (taxonomía o por defecto) y todas las queries activas
            available_topics = get_category_catalog_for_brand(filters.get('brand'))
            cur.execute("SELECT id, query FROM queries WHERE enabled = TRUE")
            qrows = cur.fetchall()
            dyn_ids = []
            for qid, qtext in qrows:
                try:
                    cat = categorize_prompt_with_ai(qtext, available_topics)
                except Exception:
                    cat = categorize_prompt(None, qtext)
                if cat == topic_filter:
                    dyn_ids.append(qid)
            if not dyn_ids:
                return jsonify({"overall_ranking": [], "by_topic": {}})
            where.append("q.id = ANY(%s)"); params.append(dyn_ids)
        where_sql = " AND ".join(where)

        # Obtener menciones con campos suficientes para detectar marcas de forma robusta
        # Incluye: key_topics (lista), texto de respuesta/título y posibles marcas en insights.payload
        cur.execute(f"""
            SELECT m.key_topics, q.topic, LOWER(COALESCE(m.response,'')) AS resp, LOWER(COALESCE(m.source_title,'')) AS title,
                   i.payload
            FROM mentions m
            JOIN queries q ON m.query_id = q.id
            LEFT JOIN insights i ON i.id = m.generated_insight_id
            WHERE {where_sql}
        """, tuple(params))
        rows = cur.fetchall()

        # Diccionario de marcas y sinónimos
        BRAND_SYNONYMS = {
            "The Core School": ["the core", "the core school", "thecore"],
            "U-TAD": ["u-tad", "utad"],
            "ECAM": ["ecam"],
            "TAI": ["tai"],
            "CES": ["ces"],
            "CEV": ["cev"],
            "FX Barcelona Film School": ["fx barcelona", "fx barcelona film school", "fx animation"],
            "Septima Ars": ["septima ars", "séptima ars"],
        }

        def detect_brands(topics_list, resp_text, title_text, payload):
            found = []
            # 1) key_topics exacto
            tlist = [str(t or '').lower().strip() for t in (topics_list or [])]
            for canon, alts in BRAND_SYNONYMS.items():
                if any(a in tlist for a in alts):
                    found.append(canon)
            # 2) payload.brands (si existe)
            try:
                brands_payload = []
                if isinstance(payload, dict):
                    brands_payload = payload.get('brands') or []
                elif payload is not None:
                    # psycopg2 devuelve JSONB como dict, pero por si acaso
                    brands_payload = []
                for canon, alts in BRAND_SYNONYMS.items():
                    if any(str(b or '').lower().strip() in alts for b in brands_payload):
                        if canon not in found:
                            found.append(canon)
            except Exception:
                pass
            # 3) búsqueda por substring en response/título
            for canon, alts in BRAND_SYNONYMS.items():
                if any(a in (resp_text or '') or a in (title_text or '') for a in alts):
                    if canon not in found:
                        found.append(canon)
            return found

        from collections import defaultdict
        overall_counts = defaultdict(int)
        topic_counts = defaultdict(lambda: defaultdict(int))
        for key_topics, topic, resp_text, title_text, payload in rows:
            brands = detect_brands(key_topics, resp_text, title_text, payload)
            if not brands:
                continue
            for b in brands:
                overall_counts[b] += 1
                topic_counts[topic or 'Uncategorized'][b] += 1

        colors = ["bg-blue-500", "bg-red-500", "bg-blue-600", "bg-yellow-500", "bg-gray-800"]
        # overall ranking
        total_mentions = sum(overall_counts.values()) or 1
        overall_sorted = sorted(overall_counts.items(), key=lambda x: x[1], reverse=True)
        overall = []
        for i, (b, c) in enumerate(overall_sorted):
            overall.append({
                "rank": i + 1,
                "name": b,
                "score": f"{(c/total_mentions)*100:.1f}%",
                "change": "+0.0%",
                "positive": True,
                "color": colors[i % len(colors)],
                "selected": b == "The Core School"
            })

        # by_topic ranking
        by_topic = {}
        for t, counts in topic_counts.items():
            tot = sum(counts.values()) or 1
            pairs = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            rk = []
            for i, (b, c) in enumerate(pairs):
                rk.append({
                    "rank": i + 1,
                    "name": b,
                    "score": f"{(c/tot)*100:.1f}%",
                    "change": "+0.0%",
                    "positive": True,
                    "color": colors[i % len(colors)],
                    "selected": b == "The Core School"
                })
            by_topic[t] = rk

        cur.close(); conn.close()
        return jsonify({"overall_ranking": overall, "by_topic": by_topic})
    except Exception as e:
        print(f"Error en get_industry_ranking: {e}")
        return jsonify({"error": str(e)}), 500

# ... (El resto de tus endpoints se quedan igual)

@app.route('/api/insights/<int:insight_id>', methods=['GET'])
def get_insight_by_id(insight_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, query_id, payload, created_at FROM insights WHERE id = %s", (insight_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        
        if not row:
            return jsonify({"error": "Insight not found"}), 404

        insight = { "id": row[0], "query_id": row[1], "payload": row[2], "created_at": row[3].isoformat() if row[3] else None }
        return jsonify(insight)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/insights', methods=['GET'])
def get_insights():
    try:
        filters = parse_filters(request)
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))

        conn = get_db_connection(); cur = conn.cursor()
        where_clauses = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where_clauses.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where_clauses.append("m.source = %s"); params.append(filters['source'])
        if filters.get('topic') and filters['topic'] != 'all':
            where_clauses.append("q.topic = %s"); params.append(filters['topic'])
        if filters.get('brand'):
            where_clauses.append("COALESCE(q.brand, '') = %s"); params.append(filters['brand'])

        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT i.id, i.query_id, i.payload, i.created_at
            FROM insights i
            JOIN mentions m ON i.id = m.generated_insight_id
            JOIN queries q ON i.query_id = q.id
            WHERE {where_sql}
            ORDER BY i.created_at DESC
            LIMIT %s OFFSET %s
        """
        cur.execute(sql, params + [limit, offset])
        rows = cur.fetchall()
        insights = [
            {"id": r[0], "query_id": r[1], "payload": r[2], "created_at": r[3].isoformat() if r[3] else None}
            for r in rows
        ]

        cur.close(); conn.close()
        return jsonify({"insights": insights, "pagination": {"limit": limit, "offset": offset, "count": len(insights)}})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sentiment', methods=['GET'])
def get_sentiment():
    try:
        filters = parse_filters(request)
        conn = get_db_connection(); cur = conn.cursor()

        where_clauses = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where_clauses.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where_clauses.append("m.source = %s"); params.append(filters['source'])
        if filters.get('topic') and filters['topic'] != 'all':
            where_clauses.append("q.topic = %s"); params.append(filters['topic'])
        if filters.get('brand'):
            where_clauses.append("COALESCE(q.brand, '') = %s"); params.append(filters['brand'])

        where_sql = " AND ".join(where_clauses)
        join_sql = "JOIN queries q ON m.query_id = q.id"

        # Promedio por día
        cur.execute(f"""
            SELECT DATE(m.created_at) AS d, AVG(COALESCE(m.sentiment,0))
            FROM mentions m
            {join_sql}
            WHERE {where_sql}
            GROUP BY DATE(m.created_at)
            ORDER BY DATE(m.created_at)
        """, tuple(params))
        ts_rows = cur.fetchall()
        timeseries = [{"date": r[0].strftime('%b %d'), "avg": float(r[1] or 0.0)} for r in ts_rows]

        # Buckets (umbrales afinados)
        cur.execute(f"""
            SELECT 
                SUM(CASE WHEN m.sentiment < -0.3 THEN 1 ELSE 0 END) AS negative,
                SUM(CASE WHEN m.sentiment BETWEEN -0.3 AND 0.3 THEN 1 ELSE 0 END) AS neutral,
                SUM(CASE WHEN m.sentiment > 0.3 THEN 1 ELSE 0 END) AS positive
            FROM mentions m
            {join_sql}
            WHERE {where_sql}
        """, tuple(params))
        bucket_row = cur.fetchone() or (0,0,0)
        distribution = {"negative": int(bucket_row[0] or 0), "neutral": int(bucket_row[1] or 0), "positive": int(bucket_row[2] or 0)}

        # Top negativas recientes (sentimiento < -0.3 y confianza >= 0.6)
        cur.execute(f"""
            SELECT m.id, m.summary, m.key_topics, m.source_title, m.source_url, m.sentiment, m.created_at
            FROM mentions m
            {join_sql}
            WHERE {where_sql} AND COALESCE(m.sentiment, 0) < -0.3 AND COALESCE(m.confidence_score, 0) >= 0.6
            ORDER BY m.sentiment ASC NULLS FIRST, m.created_at DESC
            LIMIT 20
        """, tuple(params))
        neg_rows = cur.fetchall()
        negatives = [
            {
                "id": r[0],
                "summary": r[1],
                "key_topics": r[2] or [],
                "source_title": r[3],
                "source_url": r[4],
                "sentiment": float(r[5] or 0.0),
                "created_at": r[6].isoformat() if r[6] else None,
            }
            for r in neg_rows
        ]

        # Top positivas recientes (sentimiento > 0.3 y confianza >= 0.6)
        cur.execute(f"""
            SELECT m.id, m.summary, m.key_topics, m.source_title, m.source_url, m.sentiment, m.created_at
            FROM mentions m
            {join_sql}
            WHERE {where_sql} AND COALESCE(m.sentiment, 0) > 0.3 AND COALESCE(m.confidence_score, 0) >= 0.6
            ORDER BY m.sentiment DESC NULLS LAST, m.created_at DESC
            LIMIT 20
        """, tuple(params))
        pos_rows = cur.fetchall()
        positives = [
            {
                "id": r[0],
                "summary": r[1],
                "key_topics": r[2] or [],
                "source_title": r[3],
                "source_url": r[4],
                "sentiment": float(r[5] or 0.0),
                "created_at": r[6].isoformat() if r[6] else None,
            }
            for r in pos_rows
        ]

        cur.close(); conn.close()
        return jsonify({"timeseries": timeseries, "distribution": distribution, "negatives": negatives, "positives": positives})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/topics-cloud', methods=['GET'])
def get_topics_cloud():
    try:
        filters = parse_filters(request)
        conn = get_db_connection(); cur = conn.cursor()

        where_clauses = ["m.created_at >= %s AND m.created_at < %s"]
        params = [filters['start_date'], filters['end_date']]
        join_sql = "JOIN queries q ON m.query_id = q.id"
        if filters.get('model') and filters['model'] != 'all':
            where_clauses.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where_clauses.append("m.source = %s"); params.append(filters['source'])
        if filters.get('topic') and filters['topic'] != 'all':
            where_clauses.append("q.topic = %s"); params.append(filters['topic'])
        where_sql = " AND ".join(where_clauses)

        # Desagregar key_topics tolerando TEXT[] o JSONB: convertir siempre con to_jsonb
        cur.execute(f"""
            SELECT LOWER(TRIM(topic)) AS t, COUNT(*) AS c, AVG(sent) AS avg_sentiment
            FROM (
                SELECT COALESCE(m.sentiment, 0) AS sent,
                       jsonb_array_elements_text(COALESCE(to_jsonb(m.key_topics), '[]'::jsonb)) AS topic
                FROM mentions m
                {join_sql}
                WHERE {where_sql}
            ) s
            WHERE topic IS NOT NULL AND topic <> ''
            GROUP BY LOWER(TRIM(topic))
            ORDER BY COUNT(*) DESC
            LIMIT 100
        """, tuple(params))
        rows = cur.fetchall()
        topics = [{"topic": r[0], "count": int(r[1] or 0), "avg_sentiment": float(r[2] or 0.0)} for r in rows]

        # Intento opcional de agrupación con IA para uso en Sentiment tab
        groups = []
        try:
            groups = group_topics_with_ai(topics)
        except Exception as _:
            groups = []

        cur.close(); conn.close()
        return jsonify({"topics": topics, "groups": groups})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/dashboard-kpis', methods=['GET'])
def get_dashboard_kpis():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        day_ago = datetime.now() - timedelta(hours=24)
        cur.execute("SELECT COUNT(*) FROM mentions WHERE created_at >= %s", [day_ago])
        mentions_24h = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM queries WHERE enabled = true")
        active_queries = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(*) FROM mentions WHERE created_at >= %s AND sentiment < -0.5", [day_ago])
        alerts_24h = cur.fetchone()[0] or 0
        cur.execute("SELECT COUNT(CASE WHEN sentiment > 0.2 THEN 1 END), COUNT(*) FROM mentions WHERE created_at >= %s", [day_ago])
        pos_total = cur.fetchone()
        pos = pos_total[0] or 0
        total = pos_total[1] or 0
        positive_sentiment = (pos / max(total, 1)) * 100 if total else 0
        cur.close()
        conn.close()
        
        return jsonify({
            "mentions_24h": mentions_24h, "mentions_24h_delta": 0,
            "positive_sentiment": round(positive_sentiment, 1), "positive_sentiment_delta": 0,
            "alerts_triggered": alerts_24h, "alerts_delta": 0,
            "active_queries": active_queries, "queries_delta": 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/topics', methods=['GET'])
def get_topics():
    """Lista de temas (topics) de las queries configuradas."""
    try:
        # Si hay taxonomía por brand, priorizar esas categorías
        brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
        ensure_taxonomy_table()
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT category FROM topic_taxonomy WHERE brand = %s ORDER BY category", (brand,))
        rows = cur.fetchall()
        if rows:
            topics = [r[0] for r in rows]
            cur.close(); conn.close()
            return jsonify({"topics": topics})

        # Fallback: deducir de queries
        cur.execute("""
            SELECT topic
            FROM queries
            WHERE enabled = TRUE AND topic IS NOT NULL AND topic <> ''
        """)
        raw_topics = [row[0] for row in cur.fetchall()]
        cur.close(); conn.close()
        canon_set = { canonicalize_topic(t) for t in raw_topics }
        # Ordenar por nombre traducible pero mantener claves canónicas como fuente de verdad
        topics = sorted(list(canon_set))
        return jsonify({"topics": topics})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_models():
    """Lista de modelos (engine) usados para generar menciones."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT engine
            FROM mentions
            WHERE engine IS NOT NULL AND engine <> ''
            ORDER BY engine
        """)
        models = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"models": models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Lista de fuentes (source) detectadas en menciones."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT source
            FROM mentions
            WHERE source IS NOT NULL AND source <> ''
            ORDER BY source
        """)
        sources = [row[0] for row in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"sources": sources})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompts', methods=['GET'])
def get_prompts_grouped():
    """Devuelve prompts agrupados por topic, con métricas básicas."""
    try:
        filters = parse_filters(request)
        conn = get_db_connection()
        cur = conn.cursor()

        # Catálogo de categorías (taxonomía por brand o catálogo por defecto)
        available_topics = get_category_catalog_for_brand(filters.get('brand'))

        # Obtenemos los prompts (queries) activos y sus métricas
        cur.execute(
            """
            SELECT q.id, q.query,
                   COUNT(m.id) AS executions,
                   COUNT(DISTINCT DATE(m.created_at)) AS active_days
            FROM queries q
            LEFT JOIN mentions m ON m.query_id = q.id
                 AND m.created_at >= %s AND m.created_at < %s
            WHERE q.enabled = TRUE
            GROUP BY q.id, q.query
            """,
            (filters['start_date'], filters['end_date'])
        )

        rows = cur.fetchall()

        # Cargar menciones por prompt para calcular métricas individuales de marca
        cur.execute(
            f"""
            SELECT m.query_id, m.key_topics,
                   LOWER(COALESCE(m.response,'')) AS resp,
                   LOWER(COALESCE(m.source_title,'')) AS title,
                   i.payload
            FROM mentions m
            JOIN queries q ON m.query_id = q.id
            LEFT JOIN insights i ON i.id = m.generated_insight_id
            WHERE m.created_at >= %s AND m.created_at < %s
              AND q.enabled = TRUE
            """,
            (filters['start_date'], filters['end_date'])
        )
        mention_rows = cur.fetchall()
        cur.close(); conn.close()

        # Convertimos a estructura agrupada por topic usando la nueva función de IA
        from collections import defaultdict
        # Agrupar menciones por query_id
        mentions_by_qid = defaultdict(list)

        # Diccionario de marcas y sinónimos (alineado con otros endpoints)
        BRAND_SYNONYMS = {
            "The Core School": ["the core", "the core school", "thecore"],
            "U-TAD": ["u-tad", "utad"],
            "ECAM": ["ecam"],
            "TAI": ["tai"],
            "CES": ["ces"],
            "CEV": ["cev"],
            "FX Barcelona Film School": ["fx barcelona", "fx barcelona film school", "fx animation"],
            "Septima Ars": ["septima ars", "séptima ars"],
        }

        def _normalize_list(xs):
            out = []
            if not xs:
                return out
            try:
                for t in xs:
                    s = str(t or '').lower().strip()
                    if s:
                        out.append(s)
            except Exception:
                pass
            return out

        def _detect_brands(topics_list, resp_text, title_text, payload):
            found = []
            tlist = _normalize_list(topics_list)
            # key_topics: igualdad o substring
            for canon, alts in BRAND_SYNONYMS.items():
                for a in alts:
                    if any(a == t or a in t for t in tlist):
                        found.append(canon)
                        break
            # payload.brands: igualdad o substring
            try:
                brands_payload = []
                if isinstance(payload, dict):
                    brands_payload = _normalize_list((payload.get('brands') or []))
                for canon, alts in BRAND_SYNONYMS.items():
                    for a in alts:
                        if any(a == b or a in b for b in brands_payload):
                            if canon not in found:
                                found.append(canon)
                            break
            except Exception:
                pass
            # substrings en texto/título
            txt = (resp_text or '') + ' ' + (title_text or '')
            for canon, alts in BRAND_SYNONYMS.items():
                if any(a in txt for a in alts):
                    if canon not in found:
                        found.append(canon)
            return found

        for qid, key_topics, resp, title, payload in mention_rows:
            mentions_by_qid[qid].append({
                "topics": key_topics,
                "resp": resp,
                "title": title,
                "payload": payload if isinstance(payload, dict) else {},
            })
        topics_map = defaultdict(list)
        total_days = max((filters['end_date'] - filters['start_date']).days, 1)

        prompt_items = []
        for pid, query, executions, active_days in rows:
            # --- ¡AQUÍ ESTÁ EL CAMBIO CLAVE! ---
            # Usamos la nueva función de IA para obtener la categoría
            category = categorize_prompt_with_ai(query, available_topics)
            # ------------------------------------

            visibility_score = round((active_days / total_days) * 100, 1)

            # Métricas individuales por prompt
            brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
            brand_present_responses = 0
            total_responses_prompt = 0
            brand_presence_count = 0  # veces que aparece la marca
            all_brands_presence_total = 0  # suma de presencias de todas las marcas

            for m in mentions_by_qid.get(pid, []):
                total_responses_prompt += 1
                present = _detect_brands(m.get('topics'), m.get('resp'), m.get('title'), m.get('payload'))
                if present:
                    all_brands_presence_total += len(present)
                if brand in present:
                    brand_present_responses += 1
                    brand_presence_count += 1

            visibility_score_individual = round((brand_present_responses / max(total_responses_prompt, 1)) * 100.0, 1)
            share_of_voice_individual = round((brand_presence_count / max(all_brands_presence_total, 1)) * 100.0, 1)
            prompt_items.append({
                "category": category,
                "id": pid,
                "query": query,
                "visibility_score": visibility_score,
                "visibility_score_individual": visibility_score_individual,
                "share_of_voice_individual": share_of_voice_individual,
                "executions": int(executions or 0),
            })

        group_exec_totals = defaultdict(int)
        for it in prompt_items:
            group_exec_totals[it["category"]] += it["executions"]

        for it in prompt_items:
            topic_name = it["category"]
            total_mentions_topic = max(group_exec_totals.get(topic_name, 0), 1)
            share_of_voice = round((it["executions"] / total_mentions_topic) * 100, 1)
            topics_map[topic_name].append({
                "id": it["id"],
                "query": it["query"],
                "visibility_score": it["visibility_score"],
                "share_of_voice": share_of_voice,
                "executions": it["executions"],
                # --- métricas individuales por prompt ---
                "visibility_score_individual": it["visibility_score_individual"],
                "share_of_voice_individual": it["share_of_voice_individual"],
            })

        topics = []
        for topic_name, prompts in topics_map.items():
            prompts_sorted = sorted(prompts, key=lambda p: p["visibility_score"], reverse=True)
            for idx, p in enumerate(prompts_sorted, 1):
                p["rank"] = idx
            topics.append({
                "topic": topic_name,
                "prompts": prompts_sorted,
                "topic_total_mentions": int(group_exec_totals.get(topic_name, 0)),
            })

        topics.sort(key=lambda t: t["topic_total_mentions"], reverse=True)

        return jsonify({"topics": topics})
    except Exception as e:
        print(f"Error en get_prompts_grouped: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts', methods=['POST'])
def create_prompt():
    """Crea un nuevo prompt (fila en `queries`).
    Espera JSON: { query: str, topic?: str, brand?: str, language?: str, enabled?: bool }
    Devuelve: { id, query, topic, brand, language, enabled, created_at }
    """
    try:
        payload = request.get_json(silent=True) or {}
        query_text = (payload.get('query') or '').strip()
        if not query_text:
            return jsonify({"error": "'query' es requerido"}), 400

        topic = (payload.get('topic') or None)
        brand = (payload.get('brand') or None)
        language = (payload.get('language') or 'en')
        enabled = bool(payload.get('enabled', True))

        conn = get_db_connection(); cur = conn.cursor()

        # Comprobar si ya existe un prompt con el mismo texto
        cur.execute("SELECT id, query, brand, topic, language, enabled, created_at FROM queries WHERE query = %s", (query_text,))
        row = cur.fetchone()
        if row:
            cur.close(); conn.close()
            return jsonify({
                "id": row[0], "query": row[1], "brand": row[2], "topic": row[3],
                "language": row[4], "enabled": bool(row[5]),
                "created_at": row[6].isoformat() if row[6] else None
            }), 200

        # Determinar categoría para almacenar en topic canónico (IA + fallback)
        available_topics = get_category_catalog_for_brand(brand)
        canonical_topic = categorize_prompt_with_ai(query_text, available_topics)

        cur.execute(
            """
            INSERT INTO queries (query, brand, topic, language, enabled)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, query, brand, topic, language, enabled, created_at
            """,
            (query_text, brand, canonical_topic, language, enabled)
        )
        new_row = cur.fetchone()
        conn.commit()
        cur.close(); conn.close()

        return jsonify({
            "id": new_row[0], "query": new_row[1], "brand": new_row[2], "topic": new_row[3],
            "language": new_row[4], "enabled": bool(new_row[5]),
            "created_at": new_row[6].isoformat() if new_row[6] else None
        }), 201
    except Exception as e:
        print(f"Error en create_prompt: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts/<int:query_id>', methods=['PATCH'])
def update_prompt(query_id: int):
    """Actualiza un prompt; re-categoriza automáticamente el topic si cambia query/topic."""
    try:
        payload = request.get_json(silent=True) or {}
        fields = []
        values = []

        # Preparar campos editables
        qtext = payload.get('query')
        tpc = payload.get('topic')
        brand = payload.get('brand')
        language = payload.get('language')
        enabled = payload.get('enabled')

        # Si viene query o topic, recalculamos categoría con IA
        if qtext is not None or tpc is not None:
            # traer valores actuales si faltan
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT query, topic FROM queries WHERE id = %s", (query_id,))
            row = cur.fetchone()
            if not row:
                cur.close(); conn.close()
                return jsonify({"error": "Prompt not found"}), 404
            current_query, current_topic = row
            cur.close(); conn.close()
            new_query = qtext if qtext is not None else current_query
            # determinar topics disponibles
            available_topics = get_category_catalog_for_brand(brand)
            cat = categorize_prompt_with_ai(new_query, available_topics)
            fields.append('topic = %s'); values.append(cat)
            if qtext is not None:
                fields.append('query = %s'); values.append(qtext)
        else:
            if qtext is not None:
                fields.append('query = %s'); values.append(qtext)
            if tpc is not None:
                fields.append('topic = %s'); values.append(tpc)

        if brand is not None:
            fields.append('brand = %s'); values.append(brand)
        if language is not None:
            fields.append('language = %s'); values.append(language)
        if enabled is not None:
            fields.append('enabled = %s'); values.append(bool(enabled))

        if not fields:
            return jsonify({"error": "No fields to update"}), 400

        sql = f"UPDATE queries SET {', '.join(fields)} WHERE id = %s RETURNING id, query, brand, topic, language, enabled, created_at"
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute(sql, tuple(values + [query_id]))
        row = cur.fetchone()
        conn.commit(); cur.close(); conn.close()
        if not row:
            return jsonify({"error": "Prompt not found"}), 404

        return jsonify({
            "id": row[0], "query": row[1], "brand": row[2], "topic": row[3],
            "language": row[4], "enabled": bool(row[5]),
            "created_at": row[6].isoformat() if row[6] else None
        })
    except Exception as e:
        print(f"Error en update_prompt: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts/<int:query_id>', methods=['DELETE'])
def delete_prompt(query_id: int):
    try:
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM queries WHERE id = %s", (query_id,))
        deleted = cur.rowcount
        conn.commit(); cur.close(); conn.close()
        if deleted == 0:
            return jsonify({"error": "Prompt not found"}), 404
        return jsonify({"message": f"Prompt {query_id} deleted"})
    except Exception as e:
        print(f"Error en delete_prompt: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/prompts/<int:query_id>', methods=['GET'])
def get_prompt_details(query_id: int):
    """
    Detalle de un prompt: devuelve métricas clave, datos para gráficos 
    (visibilidad y SOV a lo largo del tiempo) y sus ejecuciones.
    """
    try:
        filters = parse_filters(request)
        conn = get_db_connection()
        cur = conn.cursor()

        # 1. Obtener datos básicos del prompt
        cur.execute("SELECT query, topic, brand FROM queries WHERE id = %s", (query_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return jsonify({"error": "Prompt not found"}), 404
        query_text, topic, brand = row
        brand_to_check = brand or os.getenv('DEFAULT_BRAND', 'The Core School')

        # 2. Construir filtros de la consulta
        where_clauses = ["m.query_id = %s", "m.created_at >= %s", "m.created_at < %s"]
        params = [query_id, filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where_clauses.append("m.engine = %s")
            params.append(filters['model'])
        where_sql = " AND ".join(where_clauses)

        # 3. Obtener todas las menciones para este prompt con los filtros
        cur.execute(
            f"""
            SELECT m.id, m.created_at, m.engine, m.response,
                   m.key_topics, LOWER(COALESCE(m.response,'')) AS resp,
                   LOWER(COALESCE(m.source_title,'')) AS title, i.payload
            FROM mentions m
            LEFT JOIN insights i ON i.id = m.generated_insight_id
            WHERE {where_sql}
            ORDER BY m.created_at DESC
            """,
            tuple(params)
        )
        mention_rows = cur.fetchall()

        # 4. Calcular métricas, tendencias y ejecuciones
        total_responses_prompt = len(mention_rows)
        executions = [{"id": r[0], "created_at": r[1].isoformat(), "engine": r[2], "response": r[3]} for r in mention_rows]

        from collections import defaultdict
        daily_brand_mentions = defaultdict(int)
        daily_total_mentions = defaultdict(int)
        daily_brand_presence = defaultdict(int)
        daily_all_brands_presence = defaultdict(int)
        all_trends = set()

        for mention in mention_rows:
            _, created_at, _, _, key_topics, resp, title, payload = mention
            mention_date = created_at.date()
            daily_total_mentions[mention_date] += 1

            present_brands = _detect_brands(key_topics, resp, title, payload)
            if brand_to_check in present_brands:
                daily_brand_mentions[mention_date] += 1
                daily_brand_presence[mention_date] += 1

            if present_brands:
                daily_all_brands_presence[mention_date] += len(present_brands)

            if payload and isinstance(payload, dict):
                trends = payload.get('trends', [])
                if isinstance(trends, list):
                    for trend in trends:
                        if isinstance(trend, str): all_trends.add(trend.strip())

        # Calcular métricas totales
        total_brand_mentions = sum(daily_brand_mentions.values())
        total_brand_presence = sum(daily_brand_presence.values())
        total_all_brands_presence = sum(daily_all_brands_presence.values())

        visibility_score = round((total_brand_mentions / max(total_responses_prompt, 1)) * 100.0, 1)
        share_of_voice = round((total_brand_presence / max(total_all_brands_presence, 1)) * 100.0, 1)

        # 5. Calcular datos para los gráficos
        timeseries = []
        sov_timeseries = []
        day_iterator = filters['start_date'].date()
        while day_iterator < filters['end_date'].date():
            # Visibilidad por día
            total_day = daily_total_mentions[day_iterator]
            brand_mentions_day = daily_brand_mentions[day_iterator]
            visibility_day = (brand_mentions_day / max(total_day, 1)) * 100
            timeseries.append({"date": day_iterator.strftime('%b %d'), "value": round(visibility_day, 1)})

            # SOV por día
            brand_presence_day = daily_brand_presence[day_iterator]
            all_brands_day = daily_all_brands_presence[day_iterator]
            sov_day = (brand_presence_day / max(all_brands_day, 1)) * 100
            sov_timeseries.append({"date": day_iterator.strftime('%b %d'), "value": round(sov_day, 1)})

            day_iterator += timedelta(days=1)

        cur.close(); conn.close()

        return jsonify({
            "id": query_id,
            "query": query_text,
            "topic": topic,
            "visibility_score": visibility_score,
            "share_of_voice": share_of_voice,
            "total_executions": total_responses_prompt,
            "trends": sorted(list(all_trends)),
            "timeseries": timeseries,
            "sov_timeseries": sov_timeseries,
            "executions": executions[:100],
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/categorize', methods=['POST'])
def categorize_endpoint():
    """Devuelve categoría detectada + confianza, alternativas y sugerencia."""
    try:
        payload = request.get_json(silent=True) or {}
        query_text = payload.get('query')

        if not query_text or len((query_text or '').strip()) < 10:
            return jsonify({"category": None, "confidence": 0, "suggestion": None})

        # Determinar catálogo de categorías "generales" para clasificar
        # 1) Si existe una taxonomía de la marca, usarla
        # 2) Si no, usar las categorías por defecto (_CATEGORY_KEYWORDS)
        try:
            ensure_taxonomy_table()
            brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT category FROM topic_taxonomy WHERE brand = %s", (brand,))
            rows = cur.fetchall(); cur.close(); conn.close()
            catalog = [r[0] for r in rows] if rows else list(_CATEGORY_KEYWORDS.keys())
        except Exception:
            catalog = list(_CATEGORY_KEYWORDS.keys())

        # Paso 1: intento con el clasificador LLM acotado al catálogo
        best_from_ai = categorize_prompt_with_ai(query_text, catalog)

        # Paso 2: si la IA no logra clasificar (Inclasificable), usar heurística detallada
        detailed = None
        if best_from_ai == "Inclasificable":
            try:
                detailed = categorize_prompt_detailed(None, query_text)
            except Exception:
                detailed = None

        # Resolver categoría final y metadatos de respuesta
        category = None
        confidence = 0.8
        alternatives = []
        suggestion = None
        suggestion_is_new = False
        closest_existing = None
        closest_score = 0.0
        is_close_match = False

        if detailed:
            category = detailed.get("category") or "Inclasificable"
            confidence = float(detailed.get("confidence") or 0.8)
            alternatives = detailed.get("alternatives") or []
            suggestion = detailed.get("suggestion") or category
            suggestion_is_new = bool(detailed.get("suggestion_is_new") or False)
            closest_existing = detailed.get("closest_existing")
            closest_score = float(detailed.get("closest_score") or 0.0)
            is_close_match = bool(detailed.get("is_close_match") or False)
        else:
            category = best_from_ai
            suggestion = best_from_ai

        # Si la categoría propuesta no está en el catálogo, mapear por similitud
        if category != "Inclasificable" and category not in (catalog or []):
            mapped, score = _best_topic_by_similarity(category, catalog)
            closest_existing = mapped
            closest_score = float(score)
            if score >= 0.7:
                category = mapped
                is_close_match = True
            else:
                suggestion_is_new = True

        # Confianza ajustada según si es nueva o mapeada
        if category == "Inclasificable":
            confidence = 0.5
        else:
            confidence = 0.9 if not suggestion_is_new else max(0.7, confidence)

        return jsonify({
            "category": category,
            "confidence": confidence,
            "alternatives": alternatives,
            "suggestion": suggestion or category,
            "suggestion_is_new": suggestion_is_new,
            "closest_existing": closest_existing,
            "closest_score": closest_score,
            "is_close_match": is_close_match,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/prompts/recategorize', methods=['POST'])
def recategorize_prompts():
    """Reclasifica todos los prompts existentes según la taxonomía general.
    Body JSON (opcional): { brand?: str, limit?: int, dry_run?: bool }
    Devuelve resumen y lista de cambios.
    """
    try:
        payload = request.get_json(silent=True) or {}
        brand = payload.get('brand') or request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
        limit = int(payload.get('limit') or 0) or None
        dry_run = bool(payload.get('dry_run', False))

        # Catálogo base
        try:
            ensure_taxonomy_table()
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT category FROM topic_taxonomy WHERE brand = %s", (brand,))
            rows = cur.fetchall(); cur.close(); conn.close()
            catalog = [r[0] for r in rows] if rows else list(_CATEGORY_KEYWORDS.keys())
        except Exception:
            catalog = list(_CATEGORY_KEYWORDS.keys())

        # Cargar prompts a procesar
        conn = get_db_connection(); cur = conn.cursor()
        sql = "SELECT id, query, brand, topic FROM queries"
        params = []
        if brand:
            sql += " WHERE (brand = %s OR %s IS NULL)"
            params.extend([brand, brand])
        sql += " ORDER BY id ASC"
        if limit:
            sql += " LIMIT %s"; params.append(limit)
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()

        changes = []
        updated = 0
        unchanged = 0
        inclasificables = 0

        for qid, qtext, qbrand, old_topic in rows:
            try:
                best_from_ai = categorize_prompt_with_ai(qtext, catalog)
            except Exception:
                best_from_ai = "Inclasificable"

            final_cat = best_from_ai
            if best_from_ai == "Inclasificable":
                try:
                    detailed = categorize_prompt_detailed(None, qtext)
                    final_cat = detailed.get("category") or "Inclasificable"
                except Exception:
                    final_cat = "Inclasificable"

            if final_cat != "Inclasificable" and final_cat not in catalog:
                mapped, score = _best_topic_by_similarity(final_cat, catalog)
                if score >= 0.7:
                    final_cat = mapped
                else:
                    # mantener inclasificable para evitar ruido en catálogo
                    final_cat = "Inclasificable"

            if final_cat == (old_topic or ""):
                unchanged += 1
            else:
                if final_cat == "Inclasificable":
                    inclasificables += 1
                if not dry_run:
                    cur2 = conn.cursor()
                    cur2.execute("UPDATE queries SET topic = %s WHERE id = %s", (final_cat, qid))
                    conn.commit(); cur2.close()
                updated += 1
                changes.append({"id": qid, "old": old_topic, "new": final_cat})

        cur.close(); conn.close()

        return jsonify({
            "brand": brand,
            "catalog_size": len(catalog),
            "total": len(rows),
            "updated": updated,
            "unchanged": unchanged,
            "inclasificables": inclasificables,
            "dry_run": dry_run,
            "changes": changes,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/query-visibility/<brand>', methods=['GET'])
def get_query_visibility(brand):
    return jsonify({"brand": brand, "queries": []})

@app.route('/api/mentions/<int:mention_id>/archive', methods=['PATCH'])
def archive_mention(mention_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE mentions SET status = 'archived' WHERE id = %s", (mention_id,))
        conn.commit()
        updated_rows = cur.rowcount
        cur.close()
        conn.close()
        
        if updated_rows == 0:
            return jsonify({"error": "Mention not found"}), 404
        
        return jsonify({"message": f"Mention {mention_id} archived successfully."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)