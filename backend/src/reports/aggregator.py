import os
from typing import Dict, List, Tuple, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session


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
    # SOV de este proyecto si el nombre coincide (usamos queries.brand si existe)
    proj_brand_sql = text("SELECT COALESCE(brand, topic, 'Unknown') AS b FROM queries WHERE id=:pid")
    # Reutilizamos sesión efímera
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


