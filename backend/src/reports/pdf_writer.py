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


def add_title(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, text, 0, 1, "L")
    pdf.ln(2)


def add_paragraph(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 6, text)
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
            pdf.multi_cell(col_widths[i], 6, str(cell), border=1, ln=3, max_line_height=pdf.font_size)
        pdf.ln(0)
    pdf.ln(3)


def build_pdf(content: Dict) -> bytes:
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    kpis = content.get("kpis", {})
    add_title(pdf, "Resumen Ejecutivo")
    add_paragraph(pdf, f"Total menciones: {kpis.get('total_mentions', 0)}")
    add_paragraph(pdf, f"Sentimiento medio: {kpis.get('sentiment_avg', 0):.2f}")
    add_paragraph(pdf, f"Share of Voice: {kpis.get('sov', 0):.1f}%")

    add_title(pdf, "Evolución del Sentimiento")
    add_image(pdf, content.get("images", {}).get("sentiment_evolution"))

    add_title(pdf, "Sentimiento por Categoría")
    add_image(pdf, content.get("images", {}).get("sentiment_by_category"))

    add_title(pdf, "Temas por Sentimiento")
    add_image(pdf, content.get("images", {}).get("topics_top_bottom"))

    add_title(pdf, "Share of Voice (SOV)")
    add_image(pdf, content.get("images", {}).get("sov_pie"))

    return bytes(pdf.output(dest="S").encode("latin-1"))


