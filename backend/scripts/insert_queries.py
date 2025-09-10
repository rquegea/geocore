import psycopg2
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- NUEVAS QUERIES SOLICITADAS ---
QUERIES = [
    ("¿Que universidades tienen carreras o programas para estudiar si me gusta escribir?", "The Core School", "Curriculum & Programs", "es"),
    ("¿En que universidad puedo estudiar si me gusta el mundo del entretenimiento?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Donde puedo estudiar algo relacionado con los videojuegos en españa?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Donde puedo estudiar cine o algo relacionado con televisión?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Que estudiar si te gusta el cine y la televisión?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Donde estudiar carreras creativas con futuro en españa?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Que universidades ofrecen becas para estudiar algo con el cine?", "The Core School", "Scholarships & Cost", "es"),
    ("¿Donde ofrecen foracion para la creacion de guiones?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Que universdiades relacionadas con el mundo audiovisual tienen acuerdos con cadenas o productoras?", "The Core School", "Brand & Reputation", "es"),
    ("¿Trabajos en el sector audiovisual con buen sueldo?", "The Core School", "Employment & Jobs", "es"),
    ("¿Mejor máster en dirección de cine en madrid?", "The Core School", "Competition & Benchmarking", "es"),
    ("¿Donde puedo hacer un master online en creacion de contenido para ser influencer?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Dónde estudiar guion para series en españa?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Universidades con mejor precio en el grado en comunicación audiovisual, privadas como publicas?", "The Core School", "Competition & Benchmarking", "es"),
    ("¿Escuelas de postproducción y vfx?", "The Core School", "Curriculum & Programs", "es"),
    ("¿Hazme un analisis comparativo entre las mejores escuelas de audiovisuales de españa?", "The Core School", "Competition & Benchmarking", "es"),
    ("¿Universidades o centros de formación con mejor reputación en formación audiovisual?", "The Core School", "Brand & Reputation", "es"),
    ("¿Salidas laborales comunicación audiovisual?", "The Core School", "Employment & Jobs", "es"),
    ("¿Es difícil encontrar trabajo en la industria del cine?", "The Core School", "Employment & Jobs", "es"),
    ("¿Mejores escuelas para hacer cosas relacionadas con la television?", "The Core School", "Competition & Benchmarking", "es"),
]

def insert_thecore_queries():
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5433)),
        database=os.getenv("POSTGRES_DB", "ai_visibility"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "postgres")
    )
    cur = conn.cursor()

    # BORRAR COMPLETAMENTE todas las queries anteriores
    print("🗑️ Eliminando TODAS las queries anteriores...")
    
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