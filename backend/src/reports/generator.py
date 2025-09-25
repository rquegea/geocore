from typing import Dict

from . import aggregator
from . import plotter
from . import pdf_writer


def generate_report(project_id: int) -> bytes:
    kpis = aggregator.get_kpi_summary(project_id)
    evo = aggregator.get_sentiment_evolution(project_id)
    by_cat = aggregator.get_sentiment_by_category(project_id)
    top5, bottom5 = aggregator.get_topics_by_sentiment(project_id)

    images = {
        "sentiment_evolution": plotter.plot_sentiment_evolution(evo),
        "sentiment_by_category": plotter.plot_sentiment_by_category(by_cat),
        "topics_top_bottom": plotter.plot_topics_top_bottom(top5, bottom5),
        "sov_pie": plotter.plot_sov_pie([(name, cnt) for name, cnt in kpis.get("sov_table", [])[:6]]),
    }

    payload: Dict = {
        "kpis": kpis,
        "images": images,
        "evolution": evo,
        "categories": by_cat,
        "topics_top": top5,
        "topics_bottom": bottom5,
    }
    return pdf_writer.build_pdf(payload)


