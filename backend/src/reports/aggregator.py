import os
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import re

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from ..insight_analysis import summarize_agent_insights


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
              AND m.created_at >= :start::date
              AND m.created_at < (:end::date + INTERVAL '1 day')
            """
        )

        brand_counts_by_period: List[Dict] = []
        competitors_global: Counter = Counter()
        for (p_start, p_end) in periods:
            rows = session.execute(sql, {"project_id": project_id, "start": p_start, "end": p_end}).mappings().all()
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
