from typing import Dict, List

from . import aggregator
from . import plotter
from . import pdf_writer


def _build_kpi_rows(kpis: Dict) -> List[List[str]]:
    return [
        ["Marca", str(kpis.get("brand_name", "-"))],
        ["Total menciones", str(kpis.get("total_mentions", 0))],
        ["Sentimiento medio", f"{kpis.get('sentiment_avg', 0.0):.2f}"],
        ["SOV", f"{kpis.get('sov', 0.0):.1f}%"],
    ]


def _build_executive_summary_text(kpis: Dict) -> str:
    tm = int(kpis.get("total_mentions", 0) or 0)
    s = float(kpis.get("sentiment_avg", 0.0) or 0.0)
    sov = float(kpis.get("sov", 0.0) or 0.0)
    brand = kpis.get("brand_name", "La marca")
    tono = "positivo" if s > 0.2 else ("neutral" if -0.2 <= s <= 0.2 else "negativo")
    return (
        f"{brand} acumuló {tm} menciones en el periodo. El tono agregado fue {tono} (\n"
        f"sentimiento medio {s:.2f}). En cuota de conversación, registra un SOV del {sov:.1f}% respecto\n"
        f"al conjunto de marcas analizadas. Se recomienda reforzar contenidos en los temas con\n"
        f"sentimiento positivo alto y abordar los de menor desempeño."
    )


def generate_report(project_id: int) -> bytes:
    # 1) Agregación de datos desde BD (sesión explícita)
    session = aggregator.get_session()
    try:
        kpis = aggregator.get_kpi_summary(session, project_id)
        evo = aggregator.get_sentiment_evolution(session, project_id)
        by_cat = aggregator.get_sentiment_by_category(session, project_id)
        top5, bottom5 = aggregator.get_topics_by_sentiment(session, project_id)
    finally:
        session.close()

    # 2) Gráficos
    images = {
        "sentiment_evolution": plotter.plot_sentiment_evolution(evo),
        "sentiment_by_category": plotter.plot_sentiment_by_category(by_cat),
        "topics_top_bottom": plotter.plot_topics_top_bottom(top5, bottom5),
        # Para el SOV usamos el reparto de cuentas por marca; el pie reflejará % automáticamente
        "sov_pie": plotter.plot_sov_pie([(name, cnt) for name, cnt in kpis.get("sov_table", [])[:6]]),
    }

    # 3) Construcción del PDF sección por sección
    kpi_rows = _build_kpi_rows(kpis)
    executive_summary = _build_executive_summary_text(kpis)

    # Insights explicativos
    evo_text = ""
    if evo:
        try:
            first_s = evo[0][1]
            last_s = evo[-1][1]
            delta = last_s - first_s
            trend_word = "mejora" if delta > 0.05 else ("empeora" if delta < -0.05 else "se mantiene estable")
            min_day, min_val = min(evo, key=lambda x: x[1])
            max_day, max_val = max(evo, key=lambda x: x[1])
            evo_text = (
                f"El sentimiento {trend_word} a lo largo del periodo (Δ={delta:.2f}). "
                f"Mínimo en {min_day} ({min_val:.2f}) y máximo en {max_day} ({max_val:.2f})."
            )
        except Exception:
            evo_text = "Resumen no disponible por datos insuficientes."

    cat_text = ""
    if by_cat:
        try:
            best_cat, best_v = max(by_cat.items(), key=lambda x: x[1])
            worst_cat, worst_v = min(by_cat.items(), key=lambda x: x[1])
            cat_text = (
                f"Mejor categoría: {best_cat} ({best_v:.2f}). "
                f"Peor categoría: {worst_cat} ({worst_v:.2f}). "
                f"Priorizar comunicación en fortalezas y mitigar debilidades."
            )
        except Exception:
            cat_text = ""

    topics_text = ""
    if top5 or bottom5:
        try:
            top_str = ", ".join([f"{t} ({v:.2f})" for t, v in top5])
            bot_str = ", ".join([f"{t} ({v:.2f})" for t, v in bottom5])
            topics_text = (
                f"Temas con mayor sentimiento: {top_str}.\n"
                f"Temas con menor sentimiento: {bot_str}."
            )
        except Exception:
            topics_text = ""

    pdf = pdf_writer.ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Portada / Título
    pdf_writer.add_title(pdf, "Informe de Inteligencia Estratégica")
    pdf_writer.add_paragraph(pdf, executive_summary)

    # KPIs y SOV
    pdf_writer.add_title(pdf, "KPIs Principales y Share of Voice")
    pdf_writer.add_table(pdf, kpi_rows)
    pdf_writer.add_image(pdf, images.get("sov_pie"))

    # Análisis de Sentimiento Global
    pdf_writer.add_title(pdf, "Análisis de Sentimiento Global")
    pdf_writer.add_image(pdf, images.get("sentiment_evolution"))
    if evo_text:
        pdf_writer.add_paragraph(pdf, evo_text)

    # Desglose por Categoría
    pdf_writer.add_title(pdf, "Análisis por Categoría")
    pdf_writer.add_image(pdf, images.get("sentiment_by_category"))
    if cat_text:
        pdf_writer.add_paragraph(pdf, cat_text)

    # Temas Relevantes (Top/Bottom)
    pdf_writer.add_title(pdf, "Temas Relevantes")
    pdf_writer.add_image(pdf, images.get("topics_top_bottom"))
    if topics_text:
        pdf_writer.add_paragraph(pdf, topics_text)

    return bytes(pdf.output(dest="S").encode("latin-1"))


