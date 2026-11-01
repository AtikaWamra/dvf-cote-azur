"""Two-page executive summary (PDF) for non-technical readers.

Generated from the same tables and charts as everything else, so it is
always in sync with the data. Page 1: key figures and findings.
Page 2: the price model and the budget view.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import matplotlib
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# DejaVu ships with matplotlib, so it exists on every machine running this
# project; Helvetica (PDF base font) cannot render "m²" or "«".
_FONTS = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
pdfmetrics.registerFont(TTFont("DejaVu", str(_FONTS / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(_FONTS / "DejaVuSans-Bold.ttf")))
registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold")

INK = colors.HexColor("#0b0b0b")
INK_2 = colors.HexColor("#52514e")
BLUE = colors.HexColor("#2a78d6")
ORANGE = colors.HexColor("#eb6834")
LINE = colors.HexColor("#e6e5e0")
TILE = colors.HexColor("#f4f3ef")

H1 = ParagraphStyle("h1", fontName="DejaVu-Bold", fontSize=19, leading=23, textColor=INK)
SUB = ParagraphStyle("sub", fontName="DejaVu", fontSize=9.5, leading=13, textColor=INK_2)
H2 = ParagraphStyle("h2", fontName="DejaVu-Bold", fontSize=12, leading=16, textColor=INK,
                    spaceBefore=8, spaceAfter=4)
BODY = ParagraphStyle("b", fontName="DejaVu", fontSize=9.2, leading=12.6, textColor=INK,
                      alignment=TA_LEFT, spaceAfter=4)
KPI_V = ParagraphStyle("kv", fontName="DejaVu-Bold", fontSize=17, leading=20, textColor=INK)
KPI_L = ParagraphStyle("kl", fontName="DejaVu", fontSize=8, leading=10, textColor=INK_2)
FOOT = ParagraphStyle("f", fontName="DejaVu", fontSize=7.5, leading=9.5, textColor=INK_2)


def _md(s: str) -> str:
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def _n(x, unit=""):
    return f"{x:,.0f}".replace(",", " ") + unit


def _kpis(r: dict) -> list[tuple[str, str]]:
    ref = int(r["param"].iloc[0].annee_ref)
    a = r["a01_marche_annuel"].set_index("annee").loc[ref]
    k = [(_n(a.ventes), f"ventes de logements en {ref}"),
         (_n(a.prix_m2_median, " €"), "prix médian au m²")]
    if pd.notna(a.prix_m2_evol_pct):
        k.append((f"{a.prix_m2_evol_pct:+.1f} %".replace(".", ","), f"prix au m² vs {ref - 1}"))
    lit = r["a06_prime_littorale"].set_index("type_local")
    if "Appartement" in lit.index and pd.notna(lit.loc["Appartement"].prime_littorale_pct):
        k.append((f"{lit.loc['Appartement'].prime_littorale_pct:+.0f} %", "prime littorale (appartements)"))
    return k


def _kpi_row(k, width):
    cells = [[Paragraph(v, KPI_V), Spacer(1, 2), Paragraph(lab, KPI_L)] for v, lab in k]
    t = Table([cells], colWidths=[width / len(k)] * len(k))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TILE),
        ("LINEAFTER", (0, 0), (-2, -1), 3, colors.white),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _img(path: Path, width):
    if not path.exists():
        return Spacer(1, 1)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    return Image(str(path), width=width, height=width * h / w)


def _pair(a: Path, b: Path, width):
    half = (width - 6 * mm) / 2
    t = Table([[_img(a, half), _img(b, half)]], colWidths=[half + 3 * mm, half + 3 * mm])
    t.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t


def build(r: dict, findings: list[tuple[str, str]], img_dir: Path, out: Path,
          auteur: str = "Atika Wamra", demo: bool = False) -> Path:
    doc = SimpleDocTemplate(str(out), pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
                            topMargin=14 * mm, bottomMargin=14 * mm,
                            title="Marché immobilier des Alpes-Maritimes", author=auteur)
    W = A4[0] - 32 * mm
    ref = int(r["param"].iloc[0].annee_ref)
    au = r["audit_nettoyage"]
    s = []
    if demo:
        s.append(Paragraph("<font color='#e34948'><b>DONNÉES SYNTHÉTIQUES (mode démo) : "
                           "ne pas diffuser.</b></font>", BODY))
    s += [Paragraph("Marché immobilier des Alpes-Maritimes", H1),
          Paragraph(f"Note de synthèse · données notariales DVF · année de référence {ref} · "
                    f"{_n(au.nb_mutations.sum())} mutations analysées", SUB),
          Spacer(1, 7 * mm), _kpi_row(_kpis(r), W), Spacer(1, 5 * mm),
          Paragraph("À retenir", H2)]
    for titre, texte in findings[:6]:
        s.append(Paragraph(f"<b>{_md(titre)}.</b> {_md(texte)}", BODY))
    s += [Spacer(1, 3 * mm),
          _pair(img_dir / "05_carte_prix.png", img_dir / "02_prix_vs_volumes.png", W),
          Spacer(1, 3 * mm),
          _pair(img_dir / "04_top_communes.png", img_dir / "07_typologies.png", W),
          PageBreak(),
          Paragraph("Pour aller plus loin", H2)]
    for titre, texte in findings[6:]:
        s.append(Paragraph(f"<b>{_md(titre)}.</b> {_md(texte)}", BODY))
    s += [Spacer(1, 3 * mm),
          _pair(img_dir / "10_moteurs_prix.png", img_dir / "11_prix_brut_vs_ajuste.png", W),
          Spacer(1, 4 * mm),
          _pair(img_dir / "08_budget.png", img_dir / "06_prime_littorale.png", W),
          Spacer(1, 5 * mm),
          Paragraph("Méthode : ventes de maisons et d'appartements uniquement, une ligne par vente notariée, "
                    "ventes groupées, mixtes et aberrantes exclues avec motif tracé ; médianes publiées à "
                    "partir de 30 ventes ; modèle hédonique OLS à erreurs robustes. Source : DVF (DGFiP), "
                    f"Geo-DVF Etalab, Licence Ouverte 2.0. {auteur}, {date.today():%d/%m/%Y}.", FOOT)]
    doc.build(s)
    return out
