"""Static charts for the README and the report (matplotlib).

Design rules: one y-axis per chart (indexed series instead of dual axes),
one colour per entity (blue = coastal / apartments, orange = inland / houses),
direct labels instead of a number on every point, recessive grid.
"""
from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd

from . import config

log = logging.getLogger(__name__)

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#a3a29c"
GRID = "#e6e5e0"
BLUE = "#2a78d6"     # slot 1: coastal / apartments / price
ORANGE = "#eb6834"   # slot 2: inland / houses / volume
BLUE_LIGHT = "#bcd5f3"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10.5,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "axes.titlesize": 13,
    "axes.titleweight": "bold", "axes.titlepad": 26, "axes.titlecolor": INK, "axes.titlelocation": "left",
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "xtick.color": INK_2, "ytick.color": INK_2,
    "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.frameon": False, "legend.fontsize": 10,
})

EUR = mtick.FuncFormatter(lambda x, _: f"{x:,.0f} €".replace(",", " "))
INT = mtick.FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", " "))


def _fmt(n: float, unit: str = "") -> str:
    return f"{n:,.0f}".replace(",", " ") + unit


def _finish(fig, ax, path: Path, subtitle: str | None = None, source: bool = True):
    if subtitle:
        ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=INK_2, fontsize=10, va="bottom")
    if source:
        fig.text(0.01, 0.01, "Source : DVF (DGFiP), Geo-DVF Etalab. Ventes de logements, nettoyées.",
                 color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(path, dpi=160)
    plt.close(fig)
    log.info("  %s", path.name)


def chart_funnel(audit: pd.DataFrame, out: Path):
    df = audit.copy()
    df["label"] = df.etape.str[3:].str.replace("_", " ").str.capitalize()
    df.loc[df.etape == "99_conservee", "label"] = "Ventes conservées"
    df = df.iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [BLUE if e == "99_conservee" else MUTED for e in df.etape]
    ax.barh(df.label, df.nb_mutations, color=colors, height=0.62)
    for y, (n, p) in enumerate(zip(df.nb_mutations, df.pct, strict=True)):
        ax.text(n, y, f"  {_fmt(n)}  ({p:.1f} %)", va="center", color=INK_2, fontsize=9)
    ax.xaxis.set_major_formatter(INT)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, df.nb_mutations.max() * 1.35)
    ax.set_title("Du fichier brut aux ventes analysables")
    _finish(fig, ax, out, "Nombre de mutations par motif de rejet (une mutation = une vente notariée)")


def chart_indices(idx: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(9, 4.8))
    x = idx.annee.astype(int)
    ax.plot(x, idx.indice_prix, color=BLUE, lw=2.2, marker="o", ms=7)
    ax.plot(x, idx.indice_volume, color=ORANGE, lw=2.2, marker="o", ms=7)
    ax.axhline(100, color=MUTED, lw=1, ls="--")
    last = idx.iloc[-1]
    ax.annotate(f"Prix au m² : {last.indice_prix:.0f}", (x.iloc[-1], last.indice_prix),
                xytext=(8, 0), textcoords="offset points", color=INK, va="center", fontsize=10)
    ax.annotate(f"Volume de ventes : {last.indice_volume:.0f}", (x.iloc[-1], last.indice_volume),
                xytext=(8, 0), textcoords="offset points", color=INK, va="center", fontsize=10)
    ax.set_xticks(x)
    ax.set_xlim(x.min() - 0.3, x.max() + 1.6)
    ax.set_title("Le marché s'ajuste-t-il par les prix ou par les volumes ?")
    ax.legend(["Prix médian au m²", "Nombre de ventes"], loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2)
    _finish(fig, ax, out, f"Indice base 100 en {x.min()}")


def chart_mensuel(m: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(10, 4.6))
    d = pd.to_datetime(m.mois_debut)
    ax.bar(d, m.ventes, width=24, color=BLUE_LIGHT)
    ax.plot(d, m.ventes_12m_glissants / 12, color=BLUE, lw=2.2)
    ax.yaxis.set_major_formatter(INT)
    ax.set_title("Ventes mensuelles et tendance de fond")
    ax.legend(["Moyenne mensuelle sur 12 mois glissants", "Ventes du mois"], loc="upper right")
    _finish(fig, ax, out, "Nombre de ventes de logements par mois")


def chart_communes(c: pd.DataFrame, out: Path, top: int = 15):
    df = c.nsmallest(top, "rang").iloc[::-1]
    fig, ax = plt.subplots(figsize=(9, 6.2))
    colors = [BLUE if lit else ORANGE for lit in df.est_littorale]
    ax.barh(df.nom_commune, df.prix_m2_median, color=colors, height=0.62)
    for y, (p, e) in enumerate(zip(df.prix_m2_median, df.prix_m2_evol_pct, strict=True)):
        evol = "" if pd.isna(e) else f"   ({e:+.1f} % sur un an)"
        ax.text(p, y, f"  {_fmt(p, ' €')}{evol}", va="center", color=INK_2, fontsize=9)
    ax.xaxis.set_major_formatter(EUR)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, df.prix_m2_median.max() * 1.45)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Commune littorale"),
                       Patch(color=ORANGE, label="Arrière-pays")], loc="lower right")
    ax.set_title(f"Les {top} communes les plus chères")
    _finish(fig, ax, out, f"Prix médian au m², tous logements, communes avec au moins "
                          f"{config.MIN_VENTES_COMMUNE} ventes")


def chart_littoral(p: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(p))
    w = 0.36
    ax.bar([i - w / 2 - 0.01 for i in x], p.prix_m2_littoral, w, color=BLUE, label="Communes littorales")
    ax.bar([i + w / 2 + 0.01 for i in x], p.prix_m2_arriere_pays, w, color=ORANGE, label="Arrière-pays")
    for i, r in enumerate(p.itertuples()):
        top = max(r.prix_m2_littoral, r.prix_m2_arriere_pays)
        ax.text(i, top * 1.04, f"Prime littorale : {r.prime_littorale_pct:+.0f} %",
                ha="center", color=INK, fontsize=10, fontweight="bold")
    ax.set_xticks(list(x), p.type_local)
    ax.yaxis.set_major_formatter(EUR)
    ax.set_ylim(0, max(p.prix_m2_littoral.max(), p.prix_m2_arriere_pays.max()) * 1.2)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=2)
    ax.set_title("Combien coûte la vue mer ?")
    _finish(fig, ax, out, "Prix médian au m² selon la localisation")


def chart_typologie(t: pd.DataFrame, out: Path):
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.bar(t.typologie, t.prix_m2_median, color=BLUE, width=0.6)
    for i, r in enumerate(t.itertuples()):
        ax.text(i, r.prix_m2_median * 1.02, f"{_fmt(r.prix_m2_median, ' €')}\n{r.surface_mediane:.0f} m²",
                ha="center", va="bottom", color=INK_2, fontsize=9)
    ax.yaxis.set_major_formatter(EUR)
    ax.set_ylim(0, t.prix_m2_median.max() * 1.25)
    ax.grid(axis="x", visible=False)
    ax.set_title("Les petites surfaces, plus chères au m²")
    _finish(fig, ax, out, "Appartements : prix médian au m² et surface médiane par typologie")


def chart_budget(b: pd.DataFrame, out: Path, n: int = 8):
    df = pd.concat([b.head(n), b.tail(n)]).drop_duplicates("nom_commune")
    df = df.sort_values("surface_pour_budget_m2")
    fig, ax = plt.subplots(figsize=(9, 6.2))
    colors = [BLUE if lit else ORANGE for lit in df.est_littorale]
    ax.barh(df.nom_commune, df.surface_pour_budget_m2, color=colors, height=0.62)
    for y, s in enumerate(df.surface_pour_budget_m2):
        ax.text(s, y, f"  {s:.0f} m²", va="center", color=INK_2, fontsize=9)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, df.surface_pour_budget_m2.max() * 1.2)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=BLUE, label="Commune littorale"),
                       Patch(color=ORANGE, label="Arrière-pays")], loc="lower right")
    ax.set_title(f"Que peut-on acheter avec {_fmt(config.BUDGET_REFERENCE_EUR, ' €')} ?")
    _finish(fig, ax, out, "Surface d'appartement au prix médian du m², communes extrêmes")


def chart_focus(f: pd.DataFrame, out: Path):
    """Small multiples: one panel per commune, same scale (no colour per commune)."""
    communes = [c for c in config.COMMUNES_FOCUS if c in set(f.nom_commune)]
    if not communes:
        return
    ncol = 3
    nrow = -(-len(communes) // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(10, 2.8 * nrow + 0.6), sharey=True, sharex=True)
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]
    for ax, c in zip(axes, communes, strict=False):
        d = f[f.nom_commune == c]
        ax.plot(d.annee, d.prix_m2_median, color=BLUE, lw=2.2, marker="o", ms=6)
        ax.set_title(c, fontsize=11)
        last = d.iloc[-1]
        ax.annotate(_fmt(last.prix_m2_median, " €"), (last.annee, last.prix_m2_median),
                    xytext=(0, 9), textcoords="offset points", ha="center", fontsize=9, color=INK)
        ax.yaxis.set_major_formatter(EUR)
        ax.set_xticks(sorted(f.annee.unique()))
        ax.tick_params(axis="x", labelrotation=45)
    for ax in axes[len(communes):]:
        ax.set_visible(False)
    fig.suptitle("Appartements : prix médian au m² dans les villes clés", x=0.01, ha="left",
                 fontweight="bold", fontsize=13)
    fig.text(0.01, 0.01, "Source : DVF (DGFiP), Geo-DVF Etalab.", color=MUTED, fontsize=8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    log.info("  %s", out.name)


def _geo_paths(geojson: Path) -> dict[str, list]:
    """Commune code -> list of matplotlib Paths (exterior + holes)."""
    import json

    from matplotlib.path import Path as MPath

    out = {}
    feats = json.loads(geojson.read_text(encoding="utf-8"))["features"]
    for f in feats:
        g = f["geometry"]
        polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        paths = []
        for poly in polys:
            rings = [MPath(ring, closed=True) for ring in poly]
            paths.append(MPath.make_compound_path(*rings))
        out[f["properties"]["code"]] = paths
    return out


def _centroid(v):
    """Area-weighted centroid of a ring (shoelace formula)."""
    import numpy as np

    x, y = v[:, 0], v[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cross = x * y1 - x1 * y
    a = cross.sum() / 2
    if abs(a) < 1e-12:
        return x.mean(), y.mean()
    return ((x + x1) * cross).sum() / (6 * a), ((y + y1) * cross).sum() / (6 * a)


# Classed sequential scale (one hue, light -> dark) and its bounds in €/m²
MAP_BREAKS = [3000, 4000, 5000, 6000, 7000]
MAP_COLORS = ["#dbe8f8", "#a9c8ef", "#6fa3e3", "#2a78d6", "#1a5aa8", "#0e3a73"]
MAP_NODATA = "#e2e1dc"
MAP_SEA = "#f3f6f9"


def chart_carte(con, out: Path, geojson: Path | None = None):
    """Choropleth: each commune coloured by its median price per m² (last 3 complete years)."""
    import matplotlib.patheffects as pe
    from matplotlib.patches import Patch, PathPatch

    geojson = geojson or (config.SEEDS_DIR / "communes_06.geojson")
    if not geojson.exists():
        log.warning("  Fond de carte absent (%s) : carte ignorée", geojson.name)
        return
    df = con.execute("""
        SELECT c.code_commune, c.nom_commune, COUNT(*) AS ventes, MEDIAN(f.prix_m2) AS prix_m2
        FROM fact_ventes f JOIN dim_commune c USING (code_commune)
        JOIN dim_date d USING (date_key)
        WHERE d.annee BETWEEN (SELECT annee_ref - 2 FROM param) AND (SELECT annee_ref FROM param)
        GROUP BY ALL
    """).df()
    ref = int(con.execute("SELECT annee_ref FROM param").fetchone()[0])
    fiable = df[df.ventes >= config.MIN_VENTES_COMMUNE].set_index("code_commune")

    def couleur(p):
        for b, c in zip(MAP_BREAKS, MAP_COLORS, strict=False):
            if p < b:
                return c
        return MAP_COLORS[-1]

    paths = _geo_paths(geojson)
    fig, ax = plt.subplots(figsize=(8.6, 8.4))
    ax.set_facecolor(MAP_SEA)
    xs, ys = [], []
    for code, plist in paths.items():
        fc = couleur(fiable.loc[code, "prix_m2"]) if code in fiable.index else MAP_NODATA
        for pth in plist:
            ax.add_patch(PathPatch(pth, facecolor=fc, edgecolor="white", linewidth=0.6))
            v = pth.vertices
            xs += [v[:, 0].min(), v[:, 0].max()]
            ys += [v[:, 1].min(), v[:, 1].max()]
    ax.set_xlim(min(xs) - 0.02, max(xs) + 0.02)
    ax.set_ylim(min(ys) - 0.10, max(ys) + 0.02)
    ax.set_aspect(1 / 0.722)  # cos(43.8°): keeps distances true

    halo = [pe.withStroke(linewidth=3, foreground="white")]
    for nom in config.COMMUNES_FOCUS:
        row = df[df.nom_commune == nom]
        if row.empty or row.code_commune.iloc[0] not in paths:
            continue
        code = row.code_commune.iloc[0]
        v = max(paths[code], key=lambda p: len(p.vertices)).vertices
        x, y = _centroid(v)
        prix = f"\n{_fmt(fiable.loc[code, 'prix_m2'], ' €')}" if code in fiable.index else ""
        ax.text(x, y, nom + prix, ha="center", va="center", fontsize=8.5, color=INK,
                fontweight="bold", path_effects=halo, linespacing=1.15)
    ax.text(0.30, 0.03, "Mer Méditerranée", transform=ax.transAxes, fontsize=10,
            color="#8aa4c2", style="italic", ha="center")

    labels = [f"moins de {_fmt(MAP_BREAKS[0], ' €')}"]
    labels += [f"{_fmt(a)} à {_fmt(b, ' €')}" for a, b in zip(MAP_BREAKS[:-1], MAP_BREAKS[1:], strict=True)]
    labels += [f"{_fmt(MAP_BREAKS[-1], ' €')} et plus"]
    handles = [Patch(facecolor=c, label=lab) for c, lab in zip(MAP_COLORS, labels, strict=True)]
    handles.append(Patch(facecolor=MAP_NODATA, label=f"moins de {config.MIN_VENTES_COMMUNE} ventes"))
    ax.legend(handles=handles, title="Prix médian au m²", loc="lower right", fontsize=8.5,
              title_fontsize=9, frameon=True, facecolor="white", edgecolor=GRID)
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_title("Carte des prix : la mer fait le prix")
    fig.text(0.01, 0.01, "Source : DVF (DGFiP), Geo-DVF Etalab ; contours IGN Admin Express "
             "(france-geojson). Ventes de logements nettoyées.", color=MUTED, fontsize=8)
    ax.text(0, 1.015, f"Prix médian au m² par commune, toutes ventes de logements {ref - 2}-{ref}",
            transform=ax.transAxes, color=INK_2, fontsize=10, va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 0.97))
    fig.savefig(out, dpi=160)
    plt.close(fig)
    log.info("  %s", out.name)


def chart_effets(eff: pd.DataFrame, r2: float, out: Path):
    """Forest plot: each driver's effect on price per m², with 95 % CI."""
    df = eff.copy()
    order = {"Type de bien": 0, "Typologie": 1, "Caractéristique": 2, "Année": 3}
    df["o"] = df.groupe.map(order)
    df = df.sort_values(["o", "niveau"], ascending=[False, False]).reset_index(drop=True)
    df["label"] = df.groupe + " : " + df.niveau
    fig, ax = plt.subplots(figsize=(9, 5.6))
    y = range(len(df))
    ax.hlines(y, df.ic_bas_pct, df.ic_haut_pct, color=BLUE_LIGHT, lw=6)
    colors = [BLUE if v >= 0 else ORANGE for v in df.effet_pct]
    ax.scatter(df.effet_pct, y, color=colors, s=70, zorder=3, edgecolors=SURFACE, linewidths=1.5)
    for yy, v in zip(y, df.effet_pct, strict=True):
        ax.text(v, yy + 0.32, f"{v + 0.0:+.1f} %".replace(".", ",").replace("-0,0", "0,0"),
                ha="center", fontsize=8.5, color=INK_2)
    ax.axvline(0, color=MUTED, lw=1)
    ax.set_yticks(list(y), df.label)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f"{x:+.0f} %"))
    ax.grid(axis="y", visible=False)
    ax.set_title("Ce qui fait le prix, toutes choses égales par ailleurs")
    _finish(fig, ax, out, f"Effet sur le prix au m², IC 95 % (R² = {r2:.2f})".replace(".", ",")
                          + ". Réf. : appartement T3, 1re année")


def chart_composition(c: pd.DataFrame, ref: str, out: Path, n: int = 15):
    """Dumbbell: raw median index vs model-adjusted index per commune."""
    df = c.nlargest(n, "ventes").sort_values("indice_ajuste").reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = range(len(df))
    ax.hlines(y, df.indice_brut, df.indice_ajuste, color=GRID, lw=3)
    ax.scatter(df.indice_brut, y, color=MUTED, s=55, zorder=3, label="Écart brut (médianes)")
    ax.scatter(df.indice_ajuste, y, color=BLUE, s=70, zorder=3, edgecolors=SURFACE, linewidths=1.5,
               label="À caractéristiques égales (modèle)")
    ax.axvline(100, color=MUTED, lw=1, ls="--")
    ax.set_yticks(list(y), df.nom_commune)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=2)
    ax.set_title("Le prix brut trompe-t-il ?")
    _finish(fig, ax, out, f"Indice de prix au m², {ref} = 100. L'écart entre les points = effet "
                          "de la composition des ventes")


def make_all(con, r: dict, img_dir: Path, m=None):
    img_dir.mkdir(parents=True, exist_ok=True)
    chart_funnel(r["audit_nettoyage"], img_dir / "01_entonnoir_nettoyage.png")
    chart_indices(r["a09_indices"], img_dir / "02_prix_vs_volumes.png")
    chart_mensuel(r["a04_mensuel"], img_dir / "03_ventes_mensuelles.png")
    chart_communes(r["a03_communes"], img_dir / "04_top_communes.png")
    chart_carte(con, img_dir / "05_carte_prix.png")
    chart_littoral(r["a06_prime_littorale"], img_dir / "06_prime_littorale.png")
    chart_typologie(r["a07_typologie"], img_dir / "07_typologies.png")
    chart_budget(r["a08_budget"], img_dir / "08_budget.png")
    chart_focus(r["a10_communes_focus"], img_dir / "09_villes_cles.png")
    if m is not None:
        chart_effets(m.effects, m.r2, img_dir / "10_moteurs_prix.png")
        chart_composition(m.communes, m.ref_commune, img_dir / "11_prix_brut_vs_ajuste.png")
