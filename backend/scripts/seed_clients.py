#!/usr/bin/env python3
"""
Seed de clientes y marcas por defecto para entorno multi-tenant.

Inserta (si no existen):
  - Client: The Core School (slug: the-core) con brand: The Core School (slug: the-core)
  - Client: Lotus (slug: lotus) con brand: Lotus (slug: lotus)

Usa credenciales de POSTGRES_* o DB_* (como el resto de scripts).
"""
from __future__ import annotations

import os
import sys
from contextlib import closing

try:
    import psycopg2  # type: ignore
except Exception as e:
    raise SystemExit(f"psycopg2 es requerido para ejecutar este script: {e}")


def env(*names: str, default: str | int | None = None):
    for n in names:
        v = os.getenv(n)
        if v is not None and v != "":
            return v
    return default


def build_db_cfg() -> dict:
    return {
        "host": env("POSTGRES_HOST", "DB_HOST", default="localhost"),
        "port": int(env("POSTGRES_PORT", "DB_PORT", default=5433)),
        "dbname": env("POSTGRES_DB", "DB_NAME", default="ai_visibility"),
        "user": env("POSTGRES_USER", "DB_USER", default="postgres"),
        "password": env("POSTGRES_PASSWORD", "DB_PASSWORD", default="postgres"),
    }


def seed_clients():
    cfg = build_db_cfg()
    with closing(psycopg2.connect(**cfg)) as conn:
        with conn.cursor() as cur:
            # Asegurar tablas mínimas
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS clients (
                  id SERIAL PRIMARY KEY,
                  name TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT now()
                );
                """
            )
            cur.execute("ALTER TABLE clients ADD COLUMN IF NOT EXISTS slug TEXT UNIQUE")

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS brands (
                  id SERIAL PRIMARY KEY,
                  client_id INT REFERENCES clients(id) ON DELETE CASCADE,
                  name TEXT NOT NULL
                );
                """
            )
            cur.execute("ALTER TABLE brands ADD COLUMN IF NOT EXISTS slug TEXT UNIQUE")

            def ensure_client_with_brand(client_name: str, client_slug: str, brand_name: str, brand_slug: str) -> None:
                # Cliente
                cur.execute("SELECT id FROM clients WHERE slug = %s", (client_slug,))
                row = cur.fetchone()
                if row is None:
                    cur.execute("INSERT INTO clients(name, slug) VALUES (%s, %s) RETURNING id", (client_name, client_slug))
                    client_id = cur.fetchone()[0]
                else:
                    client_id = row[0]
                # Marca
                cur.execute("SELECT id FROM brands WHERE slug = %s AND client_id = %s", (brand_slug, client_id))
                b = cur.fetchone()
                if b is None:
                    cur.execute("INSERT INTO brands(client_id, name, slug) VALUES (%s, %s, %s)", (client_id, brand_name, brand_slug))

            ensure_client_with_brand("The Core School", "the-core", "The Core School", "the-core")
            ensure_client_with_brand("Lotus", "lotus", "Lotus", "lotus")

        conn.commit()


if __name__ == "__main__":
    try:
        seed_clients()
        print("✅ Seed completado: clients y brands por defecto listos.")
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        raise SystemExit(f"Error en seed: {e}")


