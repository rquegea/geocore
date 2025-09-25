from typing import Dict, List, Any

from . import aggregator
from . import plotter
from . import pdf_writer
from ..engines.openai_engine import fetch_response
from ..engines import strategic_prompts as s_prompts
import json
from typing import Optional


def _build_kpi_rows(kpis: Dict) -> List[List[str]]:
    return [
        ["Marca", str(kpis.get("brand_name", "-"))],
        ["Total menciones", str(kpis.get("total_mentions", 0))],
        ["Sentimiento medio", f"{kpis.get('sentiment_avg', 0.0):.2f}"],
        ["SOV", f"{kpis.get('sov', 0.0):.1f}%"],
    ]


def _extract_insights_to_json(aggregated: Dict[str, Any]) -> Dict[str, Any]:
    prompt = s_prompts.get_insight_extraction_prompt(aggregated)
    raw = fetch_response(prompt, model="gpt-4o", temperature=0.2, max_tokens=2048)
    if not raw:
        return {}
    try:
        text = raw.strip()
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        import json
        data = json.loads(text)
        return {
            "executive_summary": data.get("executive_summary", "") if isinstance(data.get("executive_summary"), str) else "",
            "executive_summary_points": data.get("key_findings", [])[:3] if isinstance(data.get("key_findings"), list) else [],
            "key_findings": data.get("key_findings", []),
            "opportunities": data.get("opportunities", []),
            "risks": data.get("risks", []),
            "strategic_recommendations": data.get("recommendations", []),
        }
    except Exception:
        return {}


def _generate_strategic_content(insights_json: Dict[str, Any], aggregated: Dict[str, Any]) -> Dict[str, str]:
    sections: Dict[str, str] = {}
    try:
        # Preferir el redactor del resumen ejecutivo basado en los insights estructurados
        if insights_json.get("executive_summary") or insights_json.get("key_findings"):
            exec_prompt = s_prompts.get_strategic_summary_prompt({
                "executive_summary": insights_json.get("executive_summary", ""),
                "key_findings": insights_json.get("key_findings", []),
            })
        else:
            exec_prompt = s_prompts.get_executive_summary_prompt(aggregated)
        sections["executive_summary"] = fetch_response(exec_prompt, model="gpt-4o", temperature=0.3, max_tokens=900)
    except Exception:
        sections["executive_summary"] = ""
    try:
        plan_prompt = s_prompts.get_strategic_plan_prompt({
            "opportunities": insights_json.get("opportunities", []),
            "risks": insights_json.get("risks", []),
            "recommendations": insights_json.get("strategic_recommendations", []),
        })
        sections["action_plan"] = fetch_response(plan_prompt, model="gpt-4o", temperature=0.3, max_tokens=1100)
    except Exception:
        sections["action_plan"] = ""
    # Sección: Análisis Competitivo
    try:
        comp_prompt = s_prompts.get_competitive_analysis_prompt(aggregated)
        sections["competitive_analysis"] = fetch_response(comp_prompt, model="gpt-4o-mini", temperature=0.3, max_tokens=900)
    except Exception:
        sections["competitive_analysis"] = ""
    # Sección: Tendencias y Anomalías
    try:
        trends_prompt = s_prompts.get_trends_anomalies_prompt(aggregated)
        sections["trends"] = fetch_response(trends_prompt, model="gpt-4o-mini", temperature=0.3, max_tokens=900)
    except Exception:
        sections["trends"] = ""
    return sections


def _analyze_cluster(cluster_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Llama al Analista de Clusters (Nivel 1) y devuelve un dict con topic_name y key_points.
    Devuelve valores seguros en caso de error.
    """
    try:
        prompt = s_prompts.get_cluster_analyst_prompt(cluster_obj)
        raw = fetch_response(prompt, model="gpt-4o-mini", temperature=0.2, max_tokens=500)
        if not raw:
            return {"topic_name": "(sin nombre)", "key_points": []}
        text = raw.strip()
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        data = json.loads(text)
        topic = data.get("topic_name") or "(sin nombre)"
        pts = data.get("key_points") or []
        if not isinstance(pts, list):
            pts = []
        return {"topic_name": str(topic), "key_points": [str(p) for p in pts][:5]}
    except Exception:
        return {"topic_name": "(sin nombre)", "key_points": []}


def _synthesize_clusters(cluster_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Llama al Sintetizador Estratégico (Nivel 2) con el resumen de clusters."""
    try:
        prompt = s_prompts.get_clusters_synthesizer_prompt([
            {
                "topic_name": c.get("topic_name", "(sin nombre)"),
                "volume": int(c.get("volume", 0)),
                "sentiment": float(c.get("sentiment", 0.0)),
            }
            for c in cluster_summaries
        ])
        raw = fetch_response(prompt, model="gpt-4o", temperature=0.2, max_tokens=900)
        if not raw:
            return {}
        text = raw.strip()
        if text.startswith("```json"):
            text = text[len("```json"):].strip()
            if text.endswith("```"):
                text = text[:-3].strip()
        return json.loads(text)
    except Exception:
        return {}


def generate_report(project_id: int, clusters: List[Dict[str, Any]] | None = None) -> bytes:
    session = aggregator.get_session()
    try:
        kpis = aggregator.get_kpi_summary(session, project_id)
        evo = aggregator.get_sentiment_evolution(session, project_id)
        by_cat = aggregator.get_sentiment_by_category(session, project_id)
        top5, bottom5 = aggregator.get_topics_by_sentiment(session, project_id)
        sov_trends = aggregator.get_share_of_voice_and_trends(session, project_id)
        agent_insights = aggregator.get_agent_insights_data(session, project_id, limit=200)
        # Nuevo: permitir inyectar clusters precalculados para evitar recomputar
        if clusters is None:
            clusters = aggregator.aggregate_clusters_for_report(session, project_id, max_rows=5000)
    finally:
        session.close()

    aggregated: Dict[str, Any] = {
        "kpis": {
            "total_mentions": kpis.get("total_mentions"),
            "average_sentiment": kpis.get("sentiment_avg"),
            "share_of_voice": kpis.get("sov"),
            "sov_by_category": sov_trends.get("current", {}).get("sov_by_category", {}),
            "competitor_mentions": sov_trends.get("current", {}).get("competitor_mentions", {}),
        },
        "client_name": kpis.get("brand_name"),
        "time_series": {
            "sentiment_per_day": [{"date": d, "average": s} for d, s in evo],
        },
        "trends": sov_trends.get("trends", {}),
        "agent_insights": agent_insights,
        # Clusters crudos para posibles usos posteriores
        "clusters_raw": clusters,
    }

    # Nivel 1: análisis por cluster
    cluster_summaries: List[Dict[str, Any]] = []
    for c in (clusters or [])[:12]:  # límite defensivo para rendimiento
        cluster_obj = {
            "count": int(c.get("count", 0)),
            "avg_sentiment": float(c.get("avg_sentiment", 0.0)),
            "top_sources": c.get("top_sources", []),
            "example_mentions": c.get("example_mentions", []),
        }
        analyzed = _analyze_cluster(cluster_obj)
        cluster_summaries.append({
            "topic_name": analyzed.get("topic_name", "(sin nombre)"),
            "key_points": analyzed.get("key_points", []),
            "volume": int(cluster_obj["count"]),
            "sentiment": float(cluster_obj["avg_sentiment"]),
        })

    # Nivel 2: síntesis estratégica a partir de clusters
    synthesis = _synthesize_clusters(cluster_summaries)

    insights_json = _extract_insights_to_json(aggregated)

    strategic_sections = _generate_strategic_content(insights_json, aggregated)
    agent_summary_text = ""
    try:
        agent_prompt = s_prompts.get_agent_insights_summary_prompt({"agent_insights": agent_insights})
        agent_summary_text = fetch_response(agent_prompt, model="gpt-4o-mini", temperature=0.3, max_tokens=700)
    except Exception:
        agent_summary_text = ""

    images = {
        "sentiment_evolution": plotter.plot_sentiment_evolution(evo),
        "sentiment_by_category": plotter.plot_sentiment_by_category(by_cat),
        "topics_top_bottom": plotter.plot_topics_top_bottom(top5, bottom5),
        "sov_pie": plotter.plot_sov_pie([(name, cnt) for name, cnt in kpis.get("sov_table", [])[:6]]),
    }

    # Nueva: Wordcloud cualitativa reciente (corpus global)
    try:
        corpus = aggregator.get_all_mentions_for_period(limit=120)
        images["wordcloud"] = plotter.plot_wordcloud_from_corpus(corpus)
    except Exception:
        images["wordcloud"] = None

    content_for_pdf: Dict[str, Any] = {
        "strategic": strategic_sections,
        "kpi_rows": _build_kpi_rows(kpis),
        "images": images,
        "agent_insights": {
            "summary": agent_summary_text,
            "buckets": agent_insights.get("buckets", {}),
        },
        # Nuevo: Clusters y Síntesis Estratégica
        "clusters": cluster_summaries,
        "clusters_synthesis": synthesis,
        # Pasamos deep_dives si el agregador los incluyó (backend app.py v1)
        "deep_dives": aggregated.get("deep_dives", []),
        "annex": {
            "evolution_text": "",
            "category_text": "",
            "topics_text": "",
        },
    }

    try:
        if evo:
            first_s = evo[0][1]
            last_s = evo[-1][1]
            delta = last_s - first_s
            trend_word = "mejora" if delta > 0.05 else ("empeora" if delta < -0.05 else "se mantiene estable")
            min_day, min_val = min(evo, key=lambda x: x[1])
            max_day, max_val = max(evo, key=lambda x: x[1])
            content_for_pdf["annex"]["evolution_text"] = (
                f"El sentimiento {trend_word} (Δ={delta:.2f}). Mínimo en {min_day} ({min_val:.2f}) y máximo en {max_day} ({max_val:.2f})."
            )
    except Exception:
        pass
    try:
        if by_cat:
            best_cat, best_v = max(by_cat.items(), key=lambda x: x[1])
            worst_cat, worst_v = min(by_cat.items(), key=lambda x: x[1])
            content_for_pdf["annex"]["category_text"] = (
                f"Mejor categoría: {best_cat} ({best_v:.2f}). Peor: {worst_cat} ({worst_v:.2f})."
            )
    except Exception:
        pass
    try:
        if top5 or bottom5:
            top_str = ", ".join([f"{t} ({v:.2f})" for t, v in top5])
            bot_str = ", ".join([f"{t} ({v:.2f})" for t, v in bottom5])
            content_for_pdf["annex"]["topics_text"] = (
                f"Top temas: {top_str}. Bottom: {bot_str}."
            )
    except Exception:
        pass

    pdf = pdf_writer.ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf_writer.add_title(pdf, "Resumen Ejecutivo")
    pdf_writer.add_paragraph(pdf, strategic_sections.get("executive_summary", ""))

    pdf_writer.add_title(pdf, "Plan de Acción Estratégico")
    pdf_writer.add_paragraph(pdf, strategic_sections.get("action_plan", ""))

    # Nuevas secciones del equipo de analistas
    if strategic_sections.get("competitive_analysis"):
        pdf_writer.add_title(pdf, "Análisis Competitivo")
        pdf_writer.add_paragraph(pdf, strategic_sections.get("competitive_analysis", ""))
    if strategic_sections.get("trends"):
        pdf_writer.add_title(pdf, "Tendencias y Señales Emergentes")
        pdf_writer.add_paragraph(pdf, strategic_sections.get("trends", ""))

    pdf_writer.add_title(pdf, "KPIs Principales y Share of Voice")
    pdf_writer.add_table(pdf, content_for_pdf["kpi_rows"])
    pdf_writer.add_image(pdf, images.get("sov_pie"))

    # Nueva sección: Temas por Clusters
    if content_for_pdf.get("clusters"):
        pdf_writer.add_title(pdf, "Temas y Hallazgos por Clusters")
        for c in content_for_pdf["clusters"][:10]:
            header = f"- {c.get('topic_name', '(sin nombre)')} | volumen: {c.get('volume', 0)} | sentiment: {float(c.get('sentiment', 0.0)):.2f}"
            pdf_writer.add_paragraph(pdf, header)
            for kp in (c.get("key_points") or [])[:3]:
                pdf_writer.add_paragraph(pdf, f"  • {kp}")

    # Nueva sección: Síntesis Estratégica a partir de Clusters
    if content_for_pdf.get("clusters_synthesis"):
        pdf_writer.add_title(pdf, "Síntesis Estratégica (basada en clusters)")
        syn = content_for_pdf["clusters_synthesis"]
        try:
            metas = syn.get("meta_narrativas") or []
            if metas:
                pdf_writer.add_paragraph(pdf, "Meta-narrativas:")
                for m in metas[:5]:
                    pdf_writer.add_paragraph(pdf, f"- {m}")
            if syn.get("oportunidad_principal"):
                pdf_writer.add_paragraph(pdf, f"Oportunidad principal: {syn['oportunidad_principal']}")
            if syn.get("riesgo_inminente"):
                pdf_writer.add_paragraph(pdf, f"Riesgo inminente: {syn['riesgo_inminente']}")
            plan = syn.get("plan_estrategico") or []
            if plan:
                pdf_writer.add_paragraph(pdf, "Plan estratégico:")
                for p in plan[:6]:
                    pdf_writer.add_paragraph(pdf, f"- {p}")
        except Exception:
            pass

    pdf_writer.add_title(pdf, "Anexo: Análisis Detallado y Visualizaciones")
    pdf_writer.add_image(pdf, images.get("sentiment_evolution"))
    if content_for_pdf["annex"].get("evolution_text"):
        pdf_writer.add_paragraph(pdf, content_for_pdf["annex"]["evolution_text"])

    pdf_writer.add_image(pdf, images.get("sentiment_by_category"))
    if content_for_pdf["annex"].get("category_text"):
        pdf_writer.add_paragraph(pdf, content_for_pdf["annex"]["category_text"])

    pdf_writer.add_image(pdf, images.get("topics_top_bottom"))
    if content_for_pdf["annex"].get("topics_text"):
        pdf_writer.add_paragraph(pdf, content_for_pdf["annex"]["topics_text"])

    # Inserta la wordcloud si está disponible
    pdf_writer.add_image(pdf, images.get("wordcloud"))

    return pdf.output(dest="S")


def generate_hybrid_report(full_data: Dict[str, Any]) -> bytes:
    """Genera un PDF híbrido que combina KPIs + gráficos + clusters + síntesis estratégica."""
    # Desempaquetar datos
    kpis = full_data.get("kpis", {})
    evo = full_data.get("time_series", {}).get("sentiment_per_day", [])
    sov = full_data.get("sov", {})
    clusters = full_data.get("clusters", [])

    # Preparar análisis de clusters (Nivel 1 y 2)
    cluster_summaries: List[Dict[str, Any]] = []
    for c in (clusters or [])[:12]:
        cluster_obj = {
            "count": int(c.get("count", 0)),
            "avg_sentiment": float(c.get("avg_sentiment", 0.0)),
            "top_sources": c.get("top_sources", []),
            "example_mentions": c.get("example_mentions", []),
        }
        analyzed = _analyze_cluster(cluster_obj)
        cluster_summaries.append({
            "topic_name": analyzed.get("topic_name", "(sin nombre)"),
            "key_points": analyzed.get("key_points", []),
            "volume": int(cluster_obj["count"]),
            "sentiment": float(cluster_obj["avg_sentiment"]),
            "examples": cluster_obj["example_mentions"][:3],
        })

    synthesis = _synthesize_clusters(cluster_summaries)

    # Construir imágenes usando plotter
    from . import plotter
    images = {}
    try:
        dates = [d for d, _ in evo]
        values = [float(v) for _, v in evo]
        images["sentiment_evolution"] = plotter.plot_sentiment_evolution(evo)
    except Exception:
        images["sentiment_evolution"] = None
    try:
        sov_list = [(name, cnt) for name, cnt in (kpis.get("sov_table", [])[:6] if kpis.get("sov_table") else [])]
        images["sov_pie"] = plotter.plot_sov_pie(sov_list)
    except Exception:
        images["sov_pie"] = None
    try:
        top5 = full_data.get("topics_top5") or []
        bottom5 = full_data.get("topics_bottom5") or []
        images["topics_top_bottom"] = plotter.plot_topics_top_bottom(top5, bottom5)
    except Exception:
        images["topics_top_bottom"] = None

    # Preparar bloques de texto estratégico a partir de síntesis
    strategic_sections = {
        "executive_summary": "",
        "action_plan": "",
        "competitive_analysis": "",
        "trends": "",
        "headline": "",
        "key_findings": [],
    }
    try:
        # Usamos síntesis para Executive y Plan si están disponibles
        if synthesis:
            exec_prompt = s_prompts.get_strategic_summary_prompt({
                "executive_summary": "" ,
                "key_findings": [kp for c in cluster_summaries for kp in c.get("key_points", [])][:6],
            })
            strategic_sections["executive_summary"] = fetch_response(exec_prompt, model="gpt-4o", temperature=0.3, max_tokens=700)
            plan_prompt = s_prompts.get_strategic_plan_prompt({
                "opportunities": [],
                "risks": [],
                "recommendations": synthesis.get("plan_estrategico", []),
            })
            strategic_sections["action_plan"] = fetch_response(plan_prompt, model="gpt-4o", temperature=0.3, max_tokens=900)
            # Headline + key findings simples a partir de puntos de clusters
            try:
                strategic_sections["key_findings"] = [kp for c in cluster_summaries for kp in c.get("key_points", [])][:4]
                if strategic_sections["executive_summary"]:
                    strategic_sections["headline"] = strategic_sections["executive_summary"].split(".")[0][:140]
            except Exception:
                pass
    except Exception:
        pass

    # Armar contenido para PDF híbrido
    kpi_rows = _build_kpi_rows(kpis)
    content_for_pdf: Dict[str, Any] = {
        "strategic": strategic_sections,
        "kpi_rows": kpi_rows,
        "images": images,
        "clusters": cluster_summaries,
        "clusters_synthesis": synthesis,
        "competitive_opportunities": full_data.get("competitive_opportunities", []),
        "kpis": kpis,
    }

    # Parte 1: nuevos gráficos solicitados
    try:
        # SOV donut (marca vs competencia) con título
        sov = full_data.get("sov", {})
        client_brand = sov.get("client_brand") or kpis.get("brand_name") or "Marca"
        current = sov.get("current", {})
        per_cat = current.get("sov_by_category", {})
        client_total = sum(int(v.get("client", 0)) for v in per_cat.values())
        # Usar SOLO el período actual, igual que el frontend
        comp_counts = current.get("competitor_mentions", {})
        sov_counts = [(client_brand, client_total)] + [(b, int(c)) for b, c in comp_counts.items()]
        # Preferir función nueva si existe; si no, caer a pie clásico
        try:
            images["part1_sov_donut"] = plotter.plot_sov_donut_centered(sov_counts, title="Share of Voice vs. Competencia")  # type: ignore[attr-defined]
        except Exception:
            images["part1_sov_donut"] = plotter.plot_sov_pie(sov_counts)
    except Exception:
        # Fallback final al SOV pie estándar si ya fue calculado más arriba
        images["part1_sov_donut"] = images.get("sov_pie")

    try:
        # Sentimiento diario (línea) con título
        evo = full_data.get("time_series", {}).get("sentiment_per_day", [])
        dates = [d for d, _ in evo]
        vals = [float(v) for _, v in evo]
        try:
            images["part1_sentiment_line"] = plotter.plot_line_series(dates, vals, title="Evolución del Sentimiento (diario)", ylabel="Sentimiento", ylim=(-1, 1), color="#2ca02c")  # type: ignore[attr-defined]
        except Exception:
            images["part1_sentiment_line"] = plotter.plot_sentiment_evolution(evo)
    except Exception:
        images["part1_sentiment_line"] = images.get("sentiment_evolution")

    try:
        # Visibilidad (línea) + ranking (si no existe la función, omitir)
        vis_series = full_data.get("visibility_timeseries") or []
        v_dates = [d for d, _ in vis_series]
        v_vals = [float(v) for _, v in vis_series]
        ranking = full_data.get("visibility_ranking") or []
        try:
            images["part1_visibility_ranking"] = plotter.plot_visibility_with_ranking(v_dates, v_vals, ranking, title="Evolución de visibilidad y ranking")  # type: ignore[attr-defined]
        except Exception:
            images["part1_visibility_ranking"] = None
    except Exception:
        images["part1_visibility_ranking"] = None

    try:
        # Distribución de menciones por categoría (porcentaje sobre total)
        curr = full_data.get("sov", {}).get("current", {})
        cat_map = curr.get("sov_by_category", {})
        dist = {k: int(v.get("total", 0)) for k, v in cat_map.items()}
        try:
            images["part1_category_distribution"] = plotter.plot_category_distribution_donut(dist, title="Distribución de menciones por categoría")  # type: ignore[attr-defined]
        except Exception:
            # Fallback: usar gráfico de sentimiento por categoría si hay datos
            sbc = full_data.get("sentiment_by_category") or {}
            images["part1_category_distribution"] = plotter.plot_sentiment_by_category(sbc)
    except Exception:
        images["part1_category_distribution"] = None

    # Renderizar PDF usando el ESQUELETO como base y añadiendo Parte 1
    try:
        from .pdf_writer import build_skeleton_with_content as _build_skeleton
    except ImportError:
        # Fallback por si el nombre cambia o el módulo aún no exporta
        from . import pdf_writer as _pw  # type: ignore
        _build_skeleton = getattr(_pw, "build_skeleton_with_content", None)
        if _build_skeleton is None:
            # Fallback final: usar la estructura vacía para no romper
            def _build_skeleton(company_name, imgs):
                return _pw.build_empty_structure_pdf(company_name)
    company = kpis.get("brand_name") or full_data.get("brand") or "Empresa"
    pdf_bytes = _build_skeleton(company, images)
    # Insertar tabla de oportunidades si existe
    try:
        if content_for_pdf.get("competitive_opportunities"):
            from .pdf_writer import ReportPDF
            # Reconstruimos el PDF para añadir la tabla (fpdf no permite abrir PDF existente fácilmente)
            # Alternativa: devolvemos el PDF base y dejamos la tabla en página adicional desde build_pdf.
            # Simpler: devolvemos el base; la tabla se renderiza en build_pdf si quisieras integrarlo ahí.
            pass
    except Exception:
        pass
    return pdf_bytes
