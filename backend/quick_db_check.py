#!/usr/bin/env python3
"""
Script COMPLETO para mostrar ABSOLUTAMENTE TODOS los datos de la base de datos
"""
import psycopg2
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'),
    port=int(os.getenv('DB_PORT', 5433)),
    database=os.getenv('DB_NAME', 'ai_visibility'),
    user=os.getenv('DB_USER', 'postgres'),
    password=os.getenv('DB_PASSWORD', 'postgres')
)

cur = conn.cursor()

print("🗄️ DUMP COMPLETO DE BASE DE DATOS AI VISIBILITY")
print("=" * 80)

# ===============================================
# 1. ESTRUCTURA DE TABLAS
# ===============================================
print("\n🏗️ ESTRUCTURA DE TABLAS:")
print("-" * 40)

tables_info = """
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
ORDER BY table_name, ordinal_position
"""

cur.execute(tables_info)
current_table = None
for row in cur.fetchall():
    table, column, data_type, nullable = row
    if table != current_table:
        print(f"\n📋 TABLA: {table.upper()}")
        current_table = table
    print(f"   {column}: {data_type} {'(NULL)' if nullable == 'YES' else '(NOT NULL)'}")

# ===============================================
# 2. QUERIES - TODAS
# ===============================================
print("\n\n🎯 TODAS LAS QUERIES:")
print("-" * 40)

cur.execute("SELECT COUNT(*) FROM queries")
total_queries = cur.fetchone()[0]
print(f"📊 Total de queries: {total_queries}")

if total_queries > 0:
    cur.execute("""
        SELECT 
            id, 
            query, 
            brand, 
            enabled, 
            created_at
        FROM queries 
        ORDER BY id
    """)
    
    for row in cur.fetchall():
        qid, query, brand, enabled, created = row
        status = "✅ ACTIVA" if enabled else "❌ DESHABILITADA"
        print(f"\nID: {qid} | {status}")
        print(f"   Query: \"{query}\"")
        print(f"   Marca: {brand}")
        print(f"   Creada: {created}")

# ===============================================
# 3. MENCIONES - TODAS CON DETALLES COMPLETOS
# ===============================================
print("\n\n💬 TODAS LAS MENCIONES:")
print("-" * 40)

cur.execute("SELECT COUNT(*) FROM mentions")
total_mentions = cur.fetchone()[0]
print(f"📊 Total de menciones: {total_mentions}")

if total_mentions > 0:
    cur.execute("""
        SELECT 
            m.id,
            m.query_id,
            m.source_url,
            m.source_title,
            m.response,
            m.source,
            m.engine,
            m.sentiment,
            m.created_at,
            m.emotion,
            m.confidence,
            q.query,
            q.brand
        FROM mentions m
        LEFT JOIN queries q ON m.query_id = q.id
        ORDER BY m.created_at DESC
    """)
    
    for i, row in enumerate(cur.fetchall(), 1):
        mid, qid, source_url, source_title, response, source, engine, sentiment, created, emotion, confidence, query, brand = row
        
        print(f"\n{'='*60}")
        print(f"📝 MENCIÓN #{i} (ID: {mid})")
        print(f"{'='*60}")
        print(f"🔗 Query ID: {qid} | Marca: {brand}")
        print(f"📱 Query: \"{query}\"")
        print(f"🌐 URL: {source_url}")
        print(f"📰 Título: {source_title}")
        print(f"🤖 Respuesta IA: {response[:200]}..." if response and len(response) > 200 else f"🤖 Respuesta IA: {response}")
        print(f"📡 Fuente: {source} | Motor: {engine}")
        print(f"😊 Sentiment: {sentiment} | Emoción: {emotion}")
        print(f"🎯 Confianza: {confidence}")
        print(f"🕐 Creada: {created}")

# ===============================================
# 4. INSIGHTS - TODOS CON PAYLOAD COMPLETO
# ===============================================
print("\n\n🧠 TODOS LOS INSIGHTS:")
print("-" * 40)

cur.execute("SELECT COUNT(*) FROM insights")
total_insights = cur.fetchone()[0]
print(f"📊 Total de insights: {total_insights}")

if total_insights > 0:
    cur.execute("""
        SELECT 
            i.id,
            i.query_id,
            i.payload,
            i.created_at,
            q.query,
            q.brand
        FROM insights i
        LEFT JOIN queries q ON i.query_id = q.id
        ORDER BY i.created_at DESC
    """)
    
    for i, row in enumerate(cur.fetchall(), 1):
        iid, qid, payload, created, query, brand = row
        
        print(f"\n{'='*60}")
        print(f"🧠 INSIGHT #{i} (ID: {iid})")
        print(f"{'='*60}")
        print(f"🔗 Query ID: {qid} | Marca: {brand}")
        print(f"📱 Query: \"{query}\"")
        print(f"🕐 Creado: {created}")
        
        if payload:
            print(f"\n📋 CONTENIDO DEL INSIGHT:")
            
            # Mostrar cada categoría del payload
            for category in ['opportunities', 'risks', 'trends', 'calls_to_action', 'summary']:
                if category in payload and payload[category]:
                    items = payload[category]
                    if isinstance(items, list):
                        print(f"\n   🎯 {category.upper()} ({len(items)} items):")
                        for j, item in enumerate(items, 1):
                            print(f"      {j}. {item}")
                    else:
                        print(f"\n   🎯 {category.upper()}: {items}")
            
            # Mostrar cualquier otra clave en el payload
            other_keys = [k for k in payload.keys() if k not in ['opportunities', 'risks', 'trends', 'calls_to_action', 'summary']]
            if other_keys:
                print(f"\n   📦 OTROS DATOS:")
                for key in other_keys:
                    print(f"      {key}: {payload[key]}")
        else:
            print("   ⚠️ Sin payload")

# ===============================================
# 5. ESTADÍSTICAS AVANZADAS
# ===============================================
print("\n\n📈 ESTADÍSTICAS AVANZADAS:")
print("-" * 40)

# Por query
print("\n🎯 ESTADÍSTICAS POR QUERY:")
cur.execute("""
    SELECT 
        q.id,
        q.query,
        q.brand,
        COUNT(m.id) as total_mentions,
        COUNT(CASE WHEN m.sentiment > 0.2 THEN 1 END) as positive_mentions,
        COUNT(CASE WHEN m.sentiment < -0.2 THEN 1 END) as negative_mentions,
        AVG(m.sentiment) as avg_sentiment,
        MIN(m.created_at) as first_mention,
        MAX(m.created_at) as last_mention
    FROM queries q
    LEFT JOIN mentions m ON q.id = m.query_id
    GROUP BY q.id, q.query, q.brand
    ORDER BY total_mentions DESC
""")

for row in cur.fetchall():
    qid, query, brand, total, positive, negative, avg_sent, first, last = row
    visibility = (positive / total * 100) if total > 0 else 0
    
    print(f"\n   📊 Query ID {qid}: \"{query[:50]}...\"")
    print(f"      Marca: {brand}")
    print(f"      Total menciones: {total}")
    print(f"      Positivas: {positive} | Negativas: {negative}")
    print(f"      Visibility: {visibility:.1f}%")
    print(f"      Sentiment promedio: {avg_sent:.3f}" if avg_sent else "      Sentiment promedio: N/A")
    print(f"      Primera mención: {first}")
    print(f"      Última mención: {last}")

# Por fuente
print("\n🌐 ESTADÍSTICAS POR FUENTE:")
cur.execute("""
    SELECT 
        source,
        COUNT(*) as mentions_count,
        AVG(sentiment) as avg_sentiment,
        COUNT(CASE WHEN sentiment > 0.2 THEN 1 END) as positive_count
    FROM mentions 
    WHERE source IS NOT NULL
    GROUP BY source
    ORDER BY mentions_count DESC
    LIMIT 10
""")

for row in cur.fetchall():
    source, count, avg_sent, positive = row
    print(f"   🏠 {source}: {count} menciones | Sentiment: {avg_sent:.3f} | Positivas: {positive}")

# Por motor de búsqueda
print("\n🔍 ESTADÍSTICAS POR MOTOR:")
cur.execute("""
    SELECT 
        engine,
        COUNT(*) as mentions_count,
        AVG(sentiment) as avg_sentiment
    FROM mentions 
    WHERE engine IS NOT NULL
    GROUP BY engine
    ORDER BY mentions_count DESC
""")

for row in cur.fetchall():
    engine, count, avg_sent = row
    print(f"   🤖 {engine}: {count} menciones | Sentiment promedio: {avg_sent:.3f}")

# Evolución temporal
print("\n📅 EVOLUCIÓN TEMPORAL (últimos 7 días):")
cur.execute("""
    SELECT 
        DATE(created_at) as day,
        COUNT(*) as mentions_count,
        AVG(sentiment) as avg_sentiment,
        COUNT(CASE WHEN sentiment > 0.2 THEN 1 END) as positive_count
    FROM mentions 
    WHERE created_at >= NOW() - INTERVAL '7 days'
    GROUP BY DATE(created_at)
    ORDER BY day DESC
""")

for row in cur.fetchall():
    day, count, avg_sent, positive = row
    print(f"   📅 {day}: {count} menciones | Sentiment: {avg_sent:.3f} | Positivas: {positive}")

# ===============================================
# 6. VERIFICACIONES DE INTEGRIDAD
# ===============================================
print("\n\n🔍 VERIFICACIONES DE INTEGRIDAD:")
print("-" * 40)

# Menciones sin query
cur.execute("SELECT COUNT(*) FROM mentions WHERE query_id NOT IN (SELECT id FROM queries)")
orphan_mentions = cur.fetchone()[0]
print(f"⚠️ Menciones huérfanas (sin query): {orphan_mentions}")

# Insights sin query
cur.execute("SELECT COUNT(*) FROM insights WHERE query_id NOT IN (SELECT id FROM queries)")
orphan_insights = cur.fetchone()[0]
print(f"⚠️ Insights huérfanos (sin query): {orphan_insights}")

# Menciones sin respuesta
cur.execute("SELECT COUNT(*) FROM mentions WHERE response IS NULL OR response = ''")
no_response = cur.fetchone()[0]
print(f"⚠️ Menciones sin respuesta IA: {no_response}")

# Menciones sin sentiment
cur.execute("SELECT COUNT(*) FROM mentions WHERE sentiment IS NULL")
no_sentiment = cur.fetchone()[0]
print(f"⚠️ Menciones sin sentiment: {no_sentiment}")

# Insights sin payload
cur.execute("SELECT COUNT(*) FROM insights WHERE payload IS NULL")
no_payload = cur.fetchone()[0]
print(f"⚠️ Insights sin payload: {no_payload}")

# ===============================================
# 7. RESUMEN FINAL
# ===============================================
print("\n\n🎯 RESUMEN FINAL:")
print("-" * 40)

cur.execute("SELECT COUNT(*) FROM queries WHERE enabled = true")
active_queries = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM mentions WHERE created_at >= NOW() - INTERVAL '24 hours'")
recent_mentions = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM insights WHERE created_at >= NOW() - INTERVAL '24 hours'")
recent_insights = cur.fetchone()[0]

cur.execute("SELECT AVG(sentiment) FROM mentions WHERE sentiment IS NOT NULL")
overall_sentiment = cur.fetchone()[0]

print(f"📊 Queries activas: {active_queries} de {total_queries}")
print(f"💬 Total menciones: {total_mentions}")
print(f"🧠 Total insights: {total_insights}")
print(f"🕐 Menciones últimas 24h: {recent_mentions}")
print(f"🕐 Insights últimos 24h: {recent_insights}")
print(f"😊 Sentiment general: {overall_sentiment:.3f}" if overall_sentiment else "😊 Sentiment general: N/A")

# Calcular visibility general
cur.execute("SELECT COUNT(*) FROM mentions WHERE sentiment > 0.2")
positive_total = cur.fetchone()[0]
if total_mentions > 0:
    overall_visibility = (positive_total / total_mentions) * 100
    print(f"👁️ Visibility general: {overall_visibility:.1f}%")

print(f"\n✅ DUMP COMPLETADO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

cur.close()
conn.close()