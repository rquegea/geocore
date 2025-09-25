import os
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from ..insight_analysis import summarize_agent_insights
from math import sqrt
from typing import TypedDict
import numpy as np

try:
    from sklearn.cluster import KMeans
except Exception:  # pragma: no cover
    KMeans = None  # type: ignore


def _db_url() -> str:
    host = os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost"))
    port = int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", 5433)))
    db = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "ai_visibility"))
    user = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
    pwd = os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "postgres"))
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{db}"


_ENGINE = None
_SessionLocal = None


def _engine():
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        _ENGINE = create_engine(_db_url(), pool_pre_ping=True, future=True)
        _SessionLocal = sessionmaker(bind=_ENGINE, autoflush=False, autocommit=False, future=True)
    return _ENGINE


def get_session() -> Session:
    _engine()
    return _SessionLocal()  # type: ignore[call-arg]


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%Y-%m-%d")


def _format_date(date_obj: datetime) -> str:
    return date_obj.strftime("%Y-%m-%d")


def _compute_previous_period(start_date: str, end_date: str) -> Tuple[str, str]:
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)
    duration_days = (end_dt - start_dt).days + 1
    prev_end = start_dt - timedelta(days=1)
    prev_start = prev_end - timedelta(days=duration_days - 1)
    return _format_date(prev_start), _format_date(prev_end)


def _compile_brand_patterns(brands: List[str]) -> List[Tuple[str, re.Pattern]]:
    patterns: List[Tuple[str, re.Pattern]] = []
    for brand in brands:
        if not brand:
            continue
        escaped = re.escape(brand.strip())
        patterns.append((brand, re.compile(rf"(?i)(?<!\w){escaped}(?!\w)")))
    return patterns


def _detect_brands(text: Optional[str], brands: List[str]) -> List[str]:
    if not text:
        return []
    found = set()
    for original, pattern in _compile_brand_patterns(brands):
        if pattern.search(text or ""):
            found.add(original)
    return list(found)


def get_kpi_summary(session: Optional[Session], project_id: int) -> Dict:
    sql = text(
        """
        SELECT COUNT(*) AS total_mentions,
               AVG(m.sentiment) AS sentiment_avg
        FROM mentions m
        JOIN queries q ON q.id = m.query_id
        WHERE q.id = :project_id
        """
    )
    sov_sql = text(
        """
        WITH brand_counts AS (
            SELECT COALESCE(q.brand, q.topic, 'Unknown') AS brand,
                   COUNT(*) AS cnt
            FROM mentions m
            JOIN queries q ON q.id = m.query_id
            GROUP BY COALESCE(q.brand, q.topic, 'Unknown')
        )
        SELECT brand, cnt FROM brand_counts ORDER BY cnt DESC
        """
    )
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        row = session.execute(sql, {"project_id": project_id}).mappings().first()
        totals = dict(row) if row else {"total_mentions": 0, "sentiment_avg": None}
        sov_rows = session.execute(sov_sql).mappings().all()
    finally:
        if own_session:
            session.close()
    total_all = sum(r["cnt"] for r in sov_rows) or 1
    proj_brand_sql = text("SELECT COALESCE(brand, topic, 'Unknown') AS b FROM queries WHERE id=:pid")
    s2 = get_session()
    try:
        brow = s2.execute(proj_brand_sql, {"pid": project_id}).first()
    finally:
        s2.close()
    brand_name = (brow[0] if brow else "Unknown")
    brand_cnt = next((r["cnt"] for r in sov_rows if r["brand"] == brand_name), 0)
    sov_pct = round(100.0 * brand_cnt / total_all, 1)
    return {
        "total_mentions": int(totals.get("total_mentions") or 0),
        "sentiment_avg": float(totals.get("sentiment_avg") or 0.0),
        "sov": sov_pct,
        "brand_name": brand_name,
        "sov_table": [(r["brand"], r["cnt"]) for r in sov_rows],
    }


def get_sentiment_evolution(session: Optional[Session], project_id: int) -> List[Tuple[str, float]]:
    sql = text(
        """
        SELECT DATE_TRUNC('day', m.created_at)::date AS d,
               AVG(m.sentiment) AS avg_s
        FROM mentions m
        JOIN queries q ON q.id = m.query_id
        WHERE q.id = :project_id
        GROUP BY 1
        ORDER BY 1
        """
    )
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        rows = session.execute(sql, {"project_id": project_id}).all()
    finally:
        if own_session:
            session.close()
    return [(r[0].strftime("%Y-%m-%d"), float(r[1] or 0.0)) for r in rows]


def get_sentiment_by_category(session: Optional[Session], project_id: int) -> Dict[str, float]:
    sql = text(
        """
        SELECT
          COALESCE((i.payload->>'category'), COALESCE(q.category, q.topic, 'Desconocida')) AS cat,
          AVG(m.sentiment) AS avg_s
        FROM mentions m
        JOIN queries q ON q.id = m.query_id
        LEFT JOIN insights i ON i.id = m.generated_insight_id
        WHERE q.id = :project_id
        GROUP BY 1
        ORDER BY 1
        """
    )
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        rows = session.execute(sql, {"project_id": project_id}).all()
    finally:
        if own_session:
            session.close()
    return {str(r[0]): float(r[1] or 0.0) for r in rows}


def get_topics_by_sentiment(session: Optional[Session], project_id: int) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    sql = text(
        """
        SELECT jsonb_array_elements_text(COALESCE(m.key_topics, '[]'::jsonb)) AS topic,
               AVG(m.sentiment) AS avg_s,
               COUNT(*) AS cnt
        FROM mentions m
        JOIN queries q ON q.id = m.query_id
        WHERE q.id = :project_id
        GROUP BY 1
        HAVING COUNT(*) >= 3
        """
    )
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        rows = session.execute(sql, {"project_id": project_id}).all()
    finally:
        if own_session:
            session.close()
    arr = [(str(r[0]), float(r[1] or 0.0)) for r in rows]
    arr.sort(key=lambda x: x[1])
    bottom5 = arr[:5]
    top5 = arr[-5:][::-1]
    return top5, bottom5


def get_share_of_voice_and_trends(
    session: Optional[Session],
    project_id: int,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    client_brand: Optional[str] = None,
) -> Dict:
    """
    Calcula SOV total y por categoría con detección de marcas en resúmenes, y deltas entre
    periodo actual y anterior. Si no se proporcionan fechas, usa todo el histórico.
    """
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        periods: List[Tuple[str, str]] = []
        if start_date and end_date:
            prev_start, prev_end = _compute_previous_period(start_date, end_date)
            periods = [(start_date, end_date), (prev_start, prev_end)]
        else:
            periods = [("1970-01-01", "2999-12-31")]

        if client_brand is None:
            brow = session.execute(text("SELECT COALESCE(brand, topic, 'Unknown') AS b FROM queries WHERE id=:pid"), {"pid": project_id}).first()
            client_brand = (brow[0] if brow else "Unknown")

        sql = text(
            """
            SELECT
              COALESCE((i.payload->>'category'), COALESCE(q.category, q.topic, 'Desconocida')) AS category,
              m.summary,
              m.sentiment,
              DATE_TRUNC('day', m.created_at)::date AS d
            FROM mentions m
            JOIN queries q ON q.id = m.query_id
            LEFT JOIN insights i ON i.id = m.generated_insight_id
            WHERE q.id = :project_id
              AND m.created_at >= CAST(:start_date AS date)
              AND m.created_at < (CAST(:end_date AS date) + INTERVAL '1 day')
            """
        )

        brand_counts_by_period: List[Dict] = []
        competitors_global: Counter = Counter()
        for (p_start, p_end) in periods:
            rows = session.execute(sql, {"project_id": project_id, "start_date": p_start, "end_date": p_end}).mappings().all()
            brands = [client_brand]
            per_category = defaultdict(lambda: {"client": 0, "total": 0, "competitors": Counter()})
            comp_mentions = Counter()
            sentiment_sum = 0.0
            sentiment_count = 0

            for r in rows:
                category = str(r["category"]) if r["category"] is not None else "Desconocida"
                summary = r.get("summary")
                sent = float(r.get("sentiment") or 0.0)
                if summary:
                    detected = _detect_brands(summary, brands)
                else:
                    detected = []
                if detected:
                    for b in detected:
                        if b == client_brand:
                            per_category[category]["client"] += 1
                        else:
                            comp_mentions[b] += 1
                            per_category[category]["competitors"][b] += 1
                        per_category[category]["total"] += 1
                sentiment_sum += sent
                sentiment_count += 1

            total_client = sum(v["client"] for v in per_category.values())
            total_comp = sum(comp_mentions.values())
            total_with_brands = float(total_client + total_comp)
            sov_total = (total_client / total_with_brands * 100.0) if total_with_brands > 0 else 0.0
            avg_sent = (sentiment_sum / float(sentiment_count)) if sentiment_count > 0 else 0.0

            brand_counts_by_period.append({
                "period": {"start": p_start, "end": p_end},
                "sov_by_category": {k: {"client": int(v["client"]), "total": int(v["total"]), "competitors": dict(v["competitors"]) } for k, v in per_category.items()},
                "competitor_mentions": dict(comp_mentions),
                "share_of_voice": sov_total,
                "average_sentiment": avg_sent,
            })
            competitors_global.update(comp_mentions)

        current = brand_counts_by_period[0]
        trends: Dict = {}
        if len(brand_counts_by_period) == 2:
            prev = brand_counts_by_period[1]
            def pct(entry: Dict) -> float:
                total_local = float(entry.get("total", 0))
                client_local = float(entry.get("client", 0))
                return (client_local / total_local * 100.0) if total_local > 0 else 0.0

            sov_delta_by_category: Dict[str, float] = {}
            for cat, entry in current.get("sov_by_category", {}).items():
                sov_delta_by_category[cat] = pct(entry) - pct(prev.get("sov_by_category", {}).get(cat, {}))

            competitor_mentions_delta = {b: int(current.get("competitor_mentions", {}).get(b, 0)) - int(prev.get("competitor_mentions", {}).get(b, 0)) for b in set(list(current.get("competitor_mentions", {}).keys()) + list(prev.get("competitor_mentions", {}).keys()))}

            trends = {
                "sentiment_delta_total": float(current.get("average_sentiment", 0.0)) - float(prev.get("average_sentiment", 0.0)),
                "sov_delta_by_category": sov_delta_by_category,
                "competitor_mentions_delta": competitor_mentions_delta,
            }

        return {
            "client_brand": client_brand,
            "current": current,
            "trends": trends,
            "competitors_seen": dict(competitors_global),
        }
    finally:
        if own_session:
            session.close()


def get_agent_insights_data(session: Optional[Session], project_id: int, limit: int = 200) -> Dict[str, Any]:
    """
    Recupera payloads de la tabla insights asociados al proyecto (query_id) y
    devuelve un resumen normalizado para prompts y PDF.
    """
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        sql = text(
            """
            SELECT i.payload
            FROM insights i
            WHERE i.query_id = :pid
            ORDER BY i.created_at DESC
            LIMIT :lim
            """
        )
        rows = session.execute(sql, {"pid": project_id, "lim": int(limit)}).mappings().all()
        payload_rows = [{"payload": r.get("payload")} for r in rows]
        return summarize_agent_insights(payload_rows)
    finally:
        if own_session:
            session.close()


def get_raw_mentions_for_topic(topic: str, limit: int = 25) -> List[str]:
    """
    Devuelve texto literal de menciones asociadas a un tema dado.
    Coincide por:
      - que el topic exista en m.key_topics (array JSON)
      - o que q.topic o q.category coincida con el tema
    """
    session = get_session()
    try:
        sql = text(
            """
            SELECT m.response
            FROM mentions m
            JOIN queries q ON q.id = m.query_id
            WHERE (
                EXISTS (
                    SELECT 1
                    FROM jsonb_array_elements_text(COALESCE(m.key_topics, '[]'::jsonb)) AS t(val)
                    WHERE lower(t.val) = lower(:topic)
                )
                OR lower(COALESCE(q.category, '')) = lower(:topic)
                OR lower(COALESCE(q.topic, '')) = lower(:topic)
            )
            ORDER BY m.created_at DESC
            LIMIT :lim
            """
        )
        rows = session.execute(sql, {"topic": topic, "lim": int(max(1, limit))}).all()
        out: List[str] = []
        for (resp,) in rows:
            if isinstance(resp, str) and resp.strip():
                out.append(resp.strip())
        return out
    finally:
        session.close()


def get_all_mentions_for_period(
    limit: int = 100,
    *,
    start_date: Optional[str] | None = None,
    end_date: Optional[str] | None = None,
    client_id: Optional[int] | None = None,
    brand_id: Optional[int] | None = None,
) -> List[str]:
    """
    Devuelve un corpus global de menciones (texto crudo) sin filtrar por tema, dentro de un
    rango de fechas. Recoge menciones recientes y representativas de TODAS las queries.

    - Usa un límite entre 100 y 150 para equilibrio coste/calidad.
    - Descarta textos vacíos y muy cortos.
    - Ordena por fecha descendente para priorizar actualidad.
    """
    from datetime import datetime, timedelta
    # Normalizar fechas
    def _to_dt(val, default):
        try:
            if isinstance(val, datetime):
                return val
            if isinstance(val, str) and val:
                return datetime.strptime(val[:10], "%Y-%m-%d")
            return default
        except Exception:
            return default

    end_dt = _to_dt(end_date, datetime.utcnow())
    start_dt = _to_dt(start_date, end_dt - timedelta(days=30))

    session = get_session()
    try:
        where = [
            "m.created_at >= :start::date",
            "m.created_at < (:end::date + INTERVAL '1 day')",
        ]
        params: Dict[str, Any] = {
            "start": start_dt.strftime("%Y-%m-%d"),
            "end": end_dt.strftime("%Y-%m-%d"),
            "lim": int(max(1, min(150, limit))),
        }
        if client_id is not None:
            where.append("q.client_id = :client_id")
            params["client_id"] = int(client_id)
        if brand_id is not None:
            where.append("q.brand_id = :brand_id")
            params["brand_id"] = int(brand_id)

        # Usar CAST(:param AS date) para evitar problemas de parseo de SQLAlchemy/psycopg2
        where_sql = ' AND '.join(where).replace(":start::date", "CAST(:start AS date)").replace(":end::date", "CAST(:end AS date)")
        sql = text(
            f"""
            SELECT m.response
            FROM mentions m
            JOIN queries q ON q.id = m.query_id
            WHERE {where_sql}
            ORDER BY m.created_at DESC
            LIMIT :lim
            """
        )

        rows = session.execute(sql, params).all()
        corpus: List[str] = []
        for (resp,) in rows:
            if not isinstance(resp, str):
                continue
            txt = resp.strip()
            if len(txt) < 40:  # descartar fragmentos demasiado cortos
                continue
            corpus.append(txt)
        return corpus
    finally:
        session.close()


class ClusterMention(TypedDict):
    id: int
    summary: str
    sentiment: float
    source: str | None
    domain: str | None
    created_at: str


class ClusterResult(TypedDict):
    cluster_id: int
    centroid: list[float]
    count: int
    avg_sentiment: float
    top_sources: list[tuple[str, int]]
    example_mentions: list[ClusterMention]


def _parse_vector_text(vec_text: str) -> list[float]:
    # Espera formato "[v1,v2,...]"; robustez ante espacios
    s = vec_text.strip()
    if s.startswith('[') and s.endswith(']'):
        s = s[1:-1]
    if not s:
        return []
    return [float(x) for x in s.replace(' ', '').split(',') if x]


def aggregate_clusters_for_report(
    session: Optional[Session],
    project_id: int,
    *,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    max_rows: int = 5000,
) -> list[ClusterResult]:
    """
    Recupera menciones con embedding no nulo en el periodo, ejecuta clustering (KMeans) y
    devuelve clusters con metadatos y ejemplos representativos.
    """
    own_session = False
    if session is None:
        session = get_session()
        own_session = True
    try:
        where = [
            "q.id = :project_id",
            "m.embedding IS NOT NULL",
        ]
        params: Dict[str, Any] = {"project_id": int(project_id), "lim": int(max_rows)}
        if start_date:
            where.append("m.created_at >= CAST(:start AS date)")
            params["start"] = start_date
        if end_date:
            where.append("m.created_at < (CAST(:end AS date) + INTERVAL '1 day')")
            params["end"] = end_date

        sql = text(
            f"""
            SELECT m.id,
                   m.summary,
                   m.sentiment,
                   m.source,
                   m.source_domain,
                   m.created_at,
                   m.embedding::text AS emb
            FROM mentions m
            JOIN queries q ON q.id = m.query_id
            WHERE {' AND '.join(where)}
            ORDER BY m.created_at DESC
            LIMIT :lim
            """
        )
        rows = session.execute(sql, params).all()
        if not rows:
            return []

        mentions: list[ClusterMention] = []
        vectors: list[list[float]] = []
        for rid, summary, sent, source, domain, created_at, emb_txt in rows:
            if not isinstance(emb_txt, str):
                continue
            vec = _parse_vector_text(emb_txt)
            if not vec:
                continue
            mentions.append({
                "id": int(rid),
                "summary": str(summary or ""),
                "sentiment": float(sent or 0.0),
                "source": str(source) if source is not None else None,
                "domain": str(domain) if domain is not None else None,
                "created_at": str(created_at),
            })
            vectors.append(vec)

        if not mentions or not vectors:
            return []

        X = np.array(vectors, dtype=np.float32)
        # Normalizar para usar similitud coseno de forma eficiente con dot product
        norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
        Xn = X / norms

        n = Xn.shape[0]
        k_default = int(max(2, min(12, round(sqrt(n / 2)))))
        if KMeans is None:
            # Fallback: un único cluster si no hay sklearn
            labels = np.zeros(n, dtype=int)
            centroids = np.mean(Xn, axis=0, keepdims=True)
        else:
            km = KMeans(n_clusters=k_default, n_init=10, max_iter=300, random_state=42)
            labels = km.fit_predict(Xn)
            centroids = km.cluster_centers_

        results: list[ClusterResult] = []
        for cid in sorted(set(int(l) for l in labels.tolist())):
            idx = np.where(labels == cid)[0]
            if idx.size == 0:
                continue
            cluster_vectors = Xn[idx]
            centroid = np.mean(cluster_vectors, axis=0)
            # cercanía por coseno = dot(centroid_norm, vec)
            cent_norm = np.linalg.norm(centroid) + 1e-12
            centroid_n = centroid / cent_norm
            scores = cluster_vectors @ centroid_n
            order = np.argsort(-scores)[:5]
            sel_idx = idx[order]
            selected: list[ClusterMention] = [mentions[i] for i in sel_idx]

            avg_sent = float(np.mean([mentions[i]["sentiment"] for i in idx]))
            from collections import Counter
            src_counter = Counter([mentions[i]["domain"] or mentions[i]["source"] or "unknown" for i in idx])
            top_sources = [(k or "unknown", int(v)) for k, v in src_counter.most_common(5)]

            results.append({
                "cluster_id": int(cid),
                "centroid": [float(x) for x in centroid.tolist()],
                "count": int(idx.size),
                "avg_sentiment": avg_sent,
                "top_sources": top_sources,
                "example_mentions": selected,
            })
        # Ordenar por tamaño desc
        results.sort(key=lambda c: c["count"], reverse=True)
        return results
    finally:
        if own_session:
            session.close()
