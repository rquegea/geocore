from typing import Dict, List, Any

from . import aggregator
from . import plotter
from . import pdf_writer
from ..engines.openai_engine import fetch_response
from ..engines import strategic_prompts as s_prompts


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
    return sections


def generate_report(project_id: int) -> bytes:
    session = aggregator.get_session()
    try:
        kpis = aggregator.get_kpi_summary(session, project_id)
        evo = aggregator.get_sentiment_evolution(session, project_id)
        by_cat = aggregator.get_sentiment_by_category(session, project_id)
        top5, bottom5 = aggregator.get_topics_by_sentiment(session, project_id)
        sov_trends = aggregator.get_share_of_voice_and_trends(session, project_id)
        agent_insights = aggregator.get_agent_insights_data(session, project_id, limit=200)
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
    }

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

    content_for_pdf: Dict[str, Any] = {
        "strategic": strategic_sections,
        "kpi_rows": _build_kpi_rows(kpis),
        "images": images,
        "agent_insights": {
            "summary": agent_summary_text,
            "buckets": agent_insights.get("buckets", {}),
        },
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

    pdf_writer.add_title(pdf, "KPIs Principales y Share of Voice")
    pdf_writer.add_table(pdf, content_for_pdf["kpi_rows"])
    pdf_writer.add_image(pdf, images.get("sov_pie"))

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

    return bytes(pdf.output(dest="S").encode("latin-1"))
