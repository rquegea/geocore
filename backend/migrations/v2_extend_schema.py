import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

DB_CFG = dict(
    host=os.getenv("POSTGRES_HOST", os.getenv("DB_HOST", "localhost")),
    port=int(os.getenv("POSTGRES_PORT", os.getenv("DB_PORT", 5433))),
    database=os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "ai_visibility")),
    user=os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres")),
    password=os.getenv("POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "postgres")),
)

def run():
    conn = psycopg2.connect(**DB_CFG)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    print("🧩 Extendiendo schema...")

    # Añadir nuevas columnas y convertir key_topics a JSONB (si aplica)
    cur.execute("""
    DO $$
    BEGIN
        -- Asegurar columna key_topics JSONB
        BEGIN
            ALTER TABLE mentions ADD COLUMN IF NOT EXISTS key_topics JSONB;
        EXCEPTION WHEN duplicate_column THEN NULL; END;

        -- Nuevos campos de gestión y observabilidad
        BEGIN
            ALTER TABLE mentions
                ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active' CHECK (status IN ('active','archived','ignored','flagged')),
                ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS spam_score REAL DEFAULT 0,
                ADD COLUMN IF NOT EXISTS duplicate_group_id TEXT,
                ADD COLUMN IF NOT EXISTS alert_triggered BOOLEAN DEFAULT FALSE,
                ADD COLUMN IF NOT EXISTS alert_reason TEXT,
                ADD COLUMN IF NOT EXISTS engine_latency_ms INTEGER,
                ADD COLUMN IF NOT EXISTS error TEXT;
        EXCEPTION WHEN others THEN NULL; END;

        -- v3: Campos de observabilidad extendidos y enriquecimiento
        BEGIN
            ALTER TABLE mentions
                ADD COLUMN IF NOT EXISTS model_name TEXT,
                ADD COLUMN IF NOT EXISTS api_status_code INTEGER,
                ADD COLUMN IF NOT EXISTS engine_request_id TEXT,
                ADD COLUMN IF NOT EXISTS input_tokens INTEGER,
                ADD COLUMN IF NOT EXISTS output_tokens INTEGER,
                ADD COLUMN IF NOT EXISTS price_usd NUMERIC(10,4),
                ADD COLUMN IF NOT EXISTS analysis_latency_ms INTEGER,
                ADD COLUMN IF NOT EXISTS total_pipeline_ms INTEGER,
                ADD COLUMN IF NOT EXISTS error_category TEXT,
                ADD COLUMN IF NOT EXISTS source_domain TEXT,
                ADD COLUMN IF NOT EXISTS source_rank INTEGER,
                ADD COLUMN IF NOT EXISTS query_text TEXT,
                ADD COLUMN IF NOT EXISTS query_topic TEXT;
        EXCEPTION WHEN others THEN NULL; END;
    END$$;
    """)

    # Índices
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_mentions_created_at ON mentions(created_at);
    CREATE INDEX IF NOT EXISTS idx_mentions_engine ON mentions(engine);
    CREATE INDEX IF NOT EXISTS idx_mentions_source ON mentions(source);
    CREATE INDEX IF NOT EXISTS idx_mentions_sentiment ON mentions(sentiment);
    CREATE INDEX IF NOT EXISTS idx_mentions_status ON mentions(status);
    CREATE INDEX IF NOT EXISTS idx_mentions_is_bot ON mentions(is_bot);
    CREATE INDEX IF NOT EXISTS idx_mentions_key_topics_gin ON mentions USING GIN (key_topics);
    CREATE INDEX IF NOT EXISTS idx_mentions_model_name ON mentions(model_name);
    CREATE INDEX IF NOT EXISTS idx_mentions_source_domain ON mentions(source_domain);
    CREATE INDEX IF NOT EXISTS idx_mentions_query_topic ON mentions(query_topic);
    """)

    # FK explícita para generated_insight_id
    cur.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE constraint_name = 'fk_mentions_generated_insight' AND table_name='mentions'
        ) THEN
            ALTER TABLE mentions
                ADD CONSTRAINT fk_mentions_generated_insight
                FOREIGN KEY (generated_insight_id)
                REFERENCES insights(id)
                ON DELETE SET NULL;
        END IF;
    END$$;
    """)

    cur.close()
    conn.close()
    print("✅ Esquema extendido correctamente.")

if __name__ == "__main__":
    run()