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
}


def _tokenize(text: str) -> set:
    t = _normalize_topic_key(text)
    return set(re.findall(r"[a-z0-9]+", t))


def categorize_prompt(topic: str | None, query_text: str | None) -> str:
    """Asigna una categoría canónica basada en palabras clave del topic y del query, brand-aware."""
    # Detect brand actual a partir de variable o fallback
    brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')

    # Cargar taxonomía custom si existe
    try:
        ensure_taxonomy_table()
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT category, COALESCE(keywords,'[]'::jsonb) FROM topic_taxonomy WHERE brand = %s", (brand,))
        rows = cur.fetchall()
        cur.close(); conn.close()
        if rows:
            categories_source = { r[0]: list(r[1] or []) }
        else:
            categories_source = _CATEGORY_KEYWORDS
    except Exception:
        categories_source = _CATEGORY_KEYWORDS

    tokens = set()
    tokens |= _tokenize(topic or '')
    tokens |= _tokenize(query_text or '')

    # puntuación por coincidencia de keywords
    best_cat = None
    best_score = 0
    for cat, keywords in categories_source.items():
        score = 0
        for kw in keywords:
            kw_tokens = set(_tokenize(kw))
            if kw_tokens & tokens:
                score += 2
            else:
                # fuzzy leve: si alguno de los tokens coincide en prefijo de 5+ caracteres
                for t in tokens:
                    if len(t) >= 5 and (t.startswith(next(iter(kw_tokens))) or next(iter(kw_tokens)).startswith(t)):
                        score += 1
                        break
        # bonus por similitud con el topic textual
        if topic:
            sim = SequenceMatcher(None, _normalize_topic_key(topic), _normalize_topic_key(cat)).ratio()
            score += int(sim * 2)
        if score > best_score:
            best_score = score
            best_cat = cat

    if best_cat and best_score >= 2:
        return best_cat

    # fallback: usa canónico del topic si existe
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

    tokens = _tokenize((topic or '') + ' ' + (query_text or ''))

    # 2) Patrones complementarios (ES/EN)
    PATTERNS = [
        (r"alumni|casos\s+de\s+exito|éxito|testimonios|trayectorias", "Alumni & Success Stories"),
        (r"plan\s+de\s+estudios|curriculum|asignaturas|programas", "Curriculum & Programs"),
        (r"empleo|empleabilidad|salidas|profesiones|trabajo|job\s*market", "Employment & Jobs"),
        (r"becas|precio|coste|costo|financiaci[oó]n|roi", "Scholarships & Cost"),
        (r"competencia|competidores|benchmark", "Competition & Benchmarking"),
        (r"marca|reputaci[oó]n|monitor", "Brand & Reputation"),
        (r"tendencias|digital|marketing|redes", "Digital Trends & Marketing"),
        (r"campus|instalaciones|recursos", "Campus & Facilities"),
        (r"innovaci[oó]n|tecnolog[ií]a|ia|ai|vr|ar", "Innovation & Technology"),
        (r"estudiantes|experiencia|expectativas", "Students & Experience"),
        (r"padres|familia|preocupaciones", "Parents & Family Concerns"),
    ]

    import re
    bonus_pattern: dict[str, int] = {}
    q = (query_text or '').lower()
    for rx, cat in PATTERNS:
        if re.search(rx, q):
            bonus_pattern[cat] = bonus_pattern.get(cat, 0) + 3

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
        score += SequenceMatcher(None, _normalize_topic_key(' '.join(tokens)), _normalize_topic_key(cat)).ratio() * 2.0
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
        if filters.get('topic') and filters['topic'] != 'all':
            where.append("q.topic = %s"); params.append(filters['topic'])
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
        # APLICAR FILTRO POR TEMA SI SE SOLICITA
        if filters.get('topic') and filters['topic'] != 'all':
            # 1) Coincidencia directa por topic de la query
            topic_filter = filters['topic']
            # 2) Ó por palabras clave de la categoría presentes en key_topics
            #    (usa taxonomía por brand si existe; si no, mapping por defecto)
            try:
                brand = request.args.get('brand') or os.getenv('DEFAULT_BRAND', 'The Core School')
                ensure_taxonomy_table()
                conn_kw = get_db_connection(); cur_kw = conn_kw.cursor()
                cur_kw.execute("SELECT COALESCE(keywords,'[]'::jsonb) FROM topic_taxonomy WHERE brand = %s AND category = %s", (brand, topic_filter))
                row_kw = cur_kw.fetchone(); cur_kw.close(); conn_kw.close()
                keywords = (row_kw[0] if row_kw else None) or _CATEGORY_KEYWORDS.get(topic_filter, [])
            except Exception:
                keywords = _CATEGORY_KEYWORDS.get(topic_filter, [])

            # normaliza keywords a minúsculas
            kw_lowers = [k.strip().lower() for k in keywords if isinstance(k, str) and k.strip()]
            if kw_lowers:
                where.append("(q.topic = %s OR EXISTS (SELECT 1 FROM jsonb_array_elements_text(COALESCE(to_jsonb(m.key_topics),'[]'::jsonb)) kt WHERE LOWER(TRIM(kt)) = ANY(%s)))")
                params.extend([topic_filter, kw_lowers])
            else:
                where.append("q.topic = %s"); params.append(topic_filter)
        where_sql = " AND ".join(where)

        # Obtener menciones con key_topics
        cur.execute(f"""
            SELECT m.key_topics, q.topic
            FROM mentions m
            JOIN queries q ON m.query_id = q.id
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

        def detect_brands(topics_list):
            found = []
            if not topics_list:
                return found
            for canon, alts in BRAND_SYNONYMS.items():
                for a in alts:
                    if any((str(t or '').lower().strip() == a) for t in topics_list):
                        found.append(canon)
                        break
            return found

        from collections import defaultdict
        overall_counts = defaultdict(int)
        topic_counts = defaultdict(lambda: defaultdict(int))
        for key_topics, topic in rows:
            brands = detect_brands(key_topics or [])
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

        cur.close(); conn.close()
        return jsonify({"topics": topics})
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
    """Devuelve prompts agrupados por topic, con métricas básicas.
    Estructura: { topics: [{ topic, prompts: [{ id, query, visibility_score, rank, share_of_voice, executions }] }] }
    """
    try:
        filters = parse_filters(request)
        conn = get_db_connection()
        cur = conn.cursor()

        # Obtenemos los prompts (queries) activos y sus métricas derivadas de menciones
        # Métricas simplificadas: visibility_score (% de días con al menos 1 mención), rank por topic (orden por score), share_of_voice (% menciones del topic), executions (conteo de menciones)

        # Total de menciones por topic (para share of voice relativo por topic)
        cur.execute(
            """
            SELECT q.topic, COUNT(m.id) AS mentions
            FROM queries q
            LEFT JOIN mentions m ON m.query_id = q.id
                 AND m.created_at >= %s AND m.created_at < %s
            WHERE q.enabled = TRUE
            GROUP BY q.topic
            """,
            (filters['start_date'], filters['end_date'])
        )
        raw_totals = { (row[0] or 'Uncategorized'): int(row[1] or 0) for row in cur.fetchall() }

        # Métricas por prompt
        cur.execute(
            """
            SELECT q.id, q.topic, q.query,
                   COUNT(m.id) AS executions,
                   COUNT(DISTINCT DATE(m.created_at)) AS active_days
            FROM queries q
            LEFT JOIN mentions m ON m.query_id = q.id
                 AND m.created_at >= %s AND m.created_at < %s
            WHERE q.enabled = TRUE
            GROUP BY q.id, q.topic, q.query
            """,
            (filters['start_date'], filters['end_date'])
        )

        rows = cur.fetchall()
        cur.close()
        conn.close()

        # Convertimos a estructura agrupada por topic
        from collections import defaultdict
        topics_map = defaultdict(list)

        # Duración en días del rango para el visibility score aproximado
        total_days = max((filters['end_date'] - filters['start_date']).days, 1)

        # Primero, calcula métricas por prompt y clasifica a una categoría
        prompt_items = []
        for pid, topic, query, executions, active_days in rows:
            category = categorize_prompt(topic, query)
            visibility_score = round((active_days / total_days) * 100, 1)
            prompt_items.append({
                "category": category,
                "id": pid,
                "query": query,
                "visibility_score": visibility_score,
                "executions": int(executions or 0),
            })

        # Totales por categoría para calcular share_of_voice dentro del grupo
        group_exec_totals = defaultdict(int)
        for it in prompt_items:
            group_exec_totals[it["category"]] += it["executions"]

        # Construye el mapa de categorías con share_of_voice relativo al grupo
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
            })

        # Asignar rank dentro de cada topic por visibility_score
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

        # Ordenamos los topics por el total de menciones descendente
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

        # Determinar categoría para almacenar en topic canónico
        canonical_topic = categorize_prompt(topic, query_text)

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

        # Si viene query o topic, recalculamos categoría
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
            new_topic = tpc if tpc is not None else current_topic
            cat = categorize_prompt(new_topic, new_query)
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
    """Detalle de un prompt (query): serie temporal, distribución por plataforma y ejecuciones.
    Responde a filtros de fecha y también acepta model/source opcionales (coherentes con el resto de endpoints).
    """
    try:
        filters = parse_filters(request)
        conn = get_db_connection()
        cur = conn.cursor()

        # Texto del prompt
        cur.execute("SELECT query, topic FROM queries WHERE id = %s", (query_id,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return jsonify({"error": "Prompt not found"}), 404
        query_text, topic = row

        # Construcción de filtros dinámicos
        where = ["m.query_id = %s", "m.created_at >= %s", "m.created_at < %s"]
        params = [query_id, filters['start_date'], filters['end_date']]
        if filters.get('model') and filters['model'] != 'all':
            where.append("m.engine = %s"); params.append(filters['model'])
        if filters.get('source') and filters['source'] != 'all':
            where.append("m.source = %s"); params.append(filters['source'])

        where_sql = " AND ".join(where)

        # Serie temporal (conteo por día)
        cur.execute(f"""
            SELECT DATE(m.created_at) AS d, COUNT(*)
            FROM mentions m
            WHERE {where_sql}
            GROUP BY DATE(m.created_at)
            ORDER BY DATE(m.created_at)
        """, tuple(params))
        ts_rows = cur.fetchall()
        timeseries = [{"date": r[0].strftime('%b %d'), "count": int(r[1] or 0)} for r in ts_rows]

        # Distribución por plataforma (engine)
        cur.execute(f"""
            SELECT COALESCE(m.engine, 'unknown') AS engine, COUNT(*)
            FROM mentions m
            WHERE {where_sql}
            GROUP BY COALESCE(m.engine, 'unknown')
            ORDER BY COUNT(*) DESC
        """, tuple(params))
        platform_rows = cur.fetchall()
        platforms = [{"name": r[0], "value": int(r[1] or 0)} for r in platform_rows]

        # Ejecuciones (últimas 100)
        cur.execute(f"""
            SELECT m.id, m.created_at, m.engine, m.source, m.response, m.sentiment
            FROM mentions m
            WHERE {where_sql}
            ORDER BY m.created_at DESC
            LIMIT 100
        """, tuple(params))
        exec_rows = cur.fetchall()
        executions = []
        for mid, created, engine, source, response, sentiment in exec_rows:
            executions.append({
                "id": mid,
                "created_at": created.isoformat() if created else None,
                "engine": engine,
                "source": source,
                "response": response,
                "sentiment": float(sentiment or 0.0),
            })

        cur.close(); conn.close()

        return jsonify({
            "id": query_id,
            "query": query_text,
            "topic": topic,
            "timeseries": timeseries,
            "platforms": platforms,
            "executions": executions,
        })
    except Exception as e:
        print(f"Error en get_prompt_details: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/categorize', methods=['POST'])
def categorize_endpoint():
    """Devuelve categoría detectada + confianza, alternativas y sugerencia."""
    try:
        payload = request.get_json(silent=True) or {}
        query_text = payload.get('query')
        topic = payload.get('topic')
        detail = categorize_prompt_detailed(topic, query_text)
        return jsonify(detail)
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