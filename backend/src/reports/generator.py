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
    # 1) Agregación de datos desde BD
    kpis = aggregator.get_kpi_summary(project_id)
    evo = aggregator.get_sentiment_evolution(project_id)
    by_cat = aggregator.get_sentiment_by_category(project_id)
    top5, bottom5 = aggregator.get_topics_by_sentiment(project_id)

    # 2) Gráficos
    images = {
        "sentiment_evolution": plotter.plot_sentiment_evolution(evo),
        "sentiment_by_category": plotter.plot_sentiment_by_category(by_cat),
        "topics_top_bottom": plotter.plot_topics_top_bottom(top5, bottom5),
        # Para el SOV usamos el reparto de cuentas por marca; el pie reflejará % automáticamente
        "sov_pie": plotter.plot_sov_pie([(name, cnt) for name, cnt in kpis.get("sov_table", [])[:6]]),
    }

    # 3) Contenido narrativo y tablas
    kpi_rows = _build_kpi_rows(kpis)
    executive_summary = _build_executive_summary_text(kpis)

    payload: Dict = {
        "title": "Informe de Inteligencia Estratégica",
        "kpis": kpis,
        "kpi_rows": kpi_rows,
        "summary": executive_summary,
        "images": images,
        "evolution": evo,
        "categories": by_cat,
        "topics_top": top5,
        "topics_bottom": bottom5,
    }
    return pdf_writer.build_pdf(payload)


