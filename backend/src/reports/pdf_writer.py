from typing import Optional, List, Tuple, Dict
from fpdf import FPDF


class ReportPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 10, "Informe Estratégico Geocore", 0, 1, "L")
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", size=8)
        self.cell(0, 10, f"Página {self.page_no()}", 0, 0, "C")


def _sanitize(text: str) -> str:
    """Convierte comillas curvas y otros caracteres Unicode comunes a ASCII apto para Helvetica.
    Elimina caracteres fuera de latin-1 para evitar FPDFUnicodeEncodingException.
    """
    if not isinstance(text, str):
        text = str(text)
    # Reemplazos comunes
    replacements = {
        "“": '"',  # U+201C
        "”": '"',  # U+201D
        "‘": "'",  # U+2018
        "’": "'",  # U+2019
        "–": "-",   # U+2013
        "—": "-",   # U+2014
        "…": "...", # U+2026
        "\xa0": " ",  # NBSP
        "•": "- ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    try:
        text = text.encode("latin-1", errors="ignore").decode("latin-1")
    except Exception:
        pass
    return text


def add_title(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _sanitize(text), 0, 1, "L")
    pdf.ln(2)


def add_paragraph(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, _sanitize(text))
    pdf.ln(1)


def add_image(pdf: ReportPDF, path: Optional[str], width: float = 180):
    if not path:
        return
    try:
        pdf.image(path, w=width)
        pdf.ln(3)
    except Exception:
        pass


def add_table(pdf: ReportPDF, rows: List[List[str]]):
    if not rows:
        return
    col_widths = [pdf.w / max(1, len(rows[0])) - 10 for _ in rows[0]]
    pdf.set_font("Helvetica", size=10)
    for r_idx, row in enumerate(rows):
        for i, cell in enumerate(row):
            pdf.multi_cell(col_widths[i], 6, _sanitize(str(cell)), border=1, ln=3, max_line_height=pdf.font_size)
        pdf.ln(0)
    pdf.ln(3)


def add_agent_insights_section(pdf: ReportPDF, agent_summary: Dict[str, str], raw_buckets: Dict[str, list] | None = None):
    """
    Inserta la sección de "Insights de Agentes" con un resumen ejecutivo y, opcionalmente,
    un anexo con elementos destacados por bucket.
    """
    if not agent_summary:
        return
    add_title(pdf, "Insights del Answer Engine")
    summary_text = agent_summary.get("summary", "")
    if summary_text:
        add_paragraph(pdf, summary_text)
    # Opcional: listas breves de ejemplos
    if raw_buckets:
        def _add_bucket(name: str, title: str, max_items: int = 5):
            items = (raw_buckets.get(name) or [])[:max_items]
            if not items:
                return
            add_title(pdf, title)
            for it in items:
                text = it.get("text") or it.get("opportunity") or it.get("risk") or it.get("trend") or "-"
                add_paragraph(pdf, f"- {text}")
        _add_bucket("opportunities", "Oportunidades destacadas")
        _add_bucket("risks", "Riesgos destacados")
        _add_bucket("trends", "Tendencias destacadas")


def build_strategic_pdf(
    *,
    narrative: Dict,
    kpi_rows: List[List[str]],
    images: Dict[str, Optional[str]],
) -> bytes:
    """
    Genera el PDF final según la estructura narrativa solicitada:
    - Página 1: Dashboard Ejecutivo (headline, evaluación, KPIs, gráfico combinado)
    - Sección 1: Análisis Estratégicos y de Mercado (Competencia, Mercado)
    - Sección 2: Análisis Cuantitativo y Correlaciones (Tendencias, Analisis Profundo)
    - Anexo: Cualitativo Global (síntesis, causa raíz, citas)
    """
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Página 1: Dashboard Ejecutivo
    headline = (narrative.get("headline") or "").strip()
    overall = (narrative.get("evaluacion_general") or "").strip()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Dashboard Ejecutivo", 0, 1, "L")
    if headline:
        pdf.set_font("Helvetica", "B", 13)
        pdf.multi_cell(0, 7, headline)
        pdf.ln(2)
    if overall:
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(0, 6, overall)
        pdf.ln(2)
    if kpi_rows:
        add_title(pdf, "KPIs")
        add_table(pdf, kpi_rows)
    if images.get("combined_vis_sent"):
        add_title(pdf, "Evolución de Visibilidad y Sentimiento")
        add_image(pdf, images.get("combined_vis_sent"))

    # Sección 1: Análisis Estratégicos y de Mercado
    pdf.add_page()
    add_title(pdf, "Sección 1: Análisis Estratégicos y de Mercado")
    comp_text = (narrative.get("analisis_competencia") or "").strip()
    if comp_text:
        add_title(pdf, "Análisis de Competencia")
        add_paragraph(pdf, comp_text)
    if images.get("sov_pie"):
        add_image(pdf, images.get("sov_pie"))
    market_text = (narrative.get("analisis_mercado") or "").strip()
    if market_text:
        add_title(pdf, "Análisis de Mercado")
        add_paragraph(pdf, market_text)
    if images.get("top_topics"):
        add_image(pdf, images.get("top_topics"))

    # Sección 2: Análisis Cuantitativo y Correlaciones
    pdf.add_page()
    add_title(pdf, "Sección 2: Análisis Cuantitativo y Correlaciones")
    if images.get("mentions_volume"):
        add_title(pdf, "Tendencias: Volumen de Menciones")
        add_image(pdf, images.get("mentions_volume"))
    deep_text = (narrative.get("analisis_profundo") or "").strip()
    if deep_text:
        add_title(pdf, "Correlaciones Transversales (Análisis Profundo)")
        add_paragraph(pdf, deep_text)

    # Anexo: Cualitativo Global
    annex = (narrative.get("cualitativo_global") or {}) if isinstance(narrative, dict) else {}
    if annex:
        pdf.add_page()
        add_title(pdf, "Anexo: Análisis Cualitativo Profundo (Global)")
        if annex.get("sintesis_del_hallazgo"):
            add_paragraph(pdf, f"Síntesis del hallazgo: {annex.get('sintesis_del_hallazgo')}")
        if annex.get("causa_raiz"):
            add_paragraph(pdf, f"Causa raíz: {annex.get('causa_raiz')}")
        citas = annex.get("citas_destacadas") or []
        if isinstance(citas, list) and citas:
            add_title(pdf, "Citas destacadas")
            for c in citas[:8]:
                add_paragraph(pdf, '"' + _sanitize(str(c)) + '"')

    # fpdf2 puede devolver bytearray cuando dest="S"; convertir de forma segura a bytes
    out = pdf.output(dest="S")
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    try:
        return bytes(str(out).encode("latin-1"))
    except Exception:
        return bytes(str(out).encode("utf-8", errors="ignore"))

def build_pdf(content: Dict) -> bytes:
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # Encabezado
    title = content.get("title") or "Informe de Inteligencia Estratégica"
    add_title(pdf, title)

    # 1) Contenido estratégico primero
    strategic = content.get("strategic", {}) if isinstance(content.get("strategic"), dict) else {}
    if strategic.get("executive_summary"):
        add_title(pdf, "Resumen Ejecutivo")
        add_paragraph(pdf, strategic.get("executive_summary", ""))
    if strategic.get("action_plan"):
        add_title(pdf, "Plan de Acción Estratégico")
        add_paragraph(pdf, strategic.get("action_plan", ""))

    # 2) Insights de Agentes (si existe)
    agent = content.get("agent_insights") or {}
    if isinstance(agent, dict) and (agent.get("summary") or agent.get("buckets")):
        add_agent_insights_section(pdf, {"summary": agent.get("summary", "")}, agent.get("buckets"))

    # 3) KPIs y SOV
    add_title(pdf, "KPIs Principales y Share of Voice")
    add_table(pdf, content.get("kpi_rows") or [])
    add_image(pdf, content.get("images", {}).get("sov_pie"))

    # 4) Anexo: visualizaciones y análisis detallado
    add_title(pdf, "Anexo: Análisis Detallado y Visualizaciones")
    add_image(pdf, content.get("images", {}).get("sentiment_evolution"))
    add_image(pdf, content.get("images", {}).get("sentiment_by_category"))
    add_image(pdf, content.get("images", {}).get("topics_top_bottom"))

    # 5) Anexo: Análisis Cualitativo Profundo
    deep_dives = (content.get("deep_dives") or []) if isinstance(content, dict) else []
    if isinstance(deep_dives, list) and deep_dives:
        add_title(pdf, "Anexo: Análisis Cualitativo Profundo")
        for item in deep_dives:
            try:
                tema = str((item or {}).get("tema") or "Tema")
                add_title(pdf, f"Tema: {tema}")
                sint = (item or {}).get("sintesis_del_hallazgo") or ""
                causa = (item or {}).get("causa_raiz") or ""
                citas = (item or {}).get("citas_destacadas") or []
                if sint:
                    add_paragraph(pdf, f"Síntesis: {sint}")
                if causa:
                    add_paragraph(pdf, f"Causa raíz: {causa}")
                if isinstance(citas, list) and citas:
                    add_paragraph(pdf, "Citas destacadas:")
                    for c in citas[:6]:
                        add_paragraph(pdf, f"\u201C{str(c)}\u201D")
            except Exception:
                continue

    out = pdf.output(dest="S")
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    try:
        return bytes(str(out).encode("latin-1"))
    except Exception:
        return bytes(str(out).encode("utf-8", errors="ignore"))


