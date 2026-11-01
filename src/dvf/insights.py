"""Turn analysis tables into written, decision-oriented findings.

Every number in the text is computed from the data; nothing is hand-typed.
When the data is refreshed, the findings rewrite themselves.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from . import config


def _n(x, unit=""):
    return f"{x:,.0f}".replace(",", " ") + unit


def _pct(x):
    return f"{x:+.1f} %".replace(".", ",")


def _d(x):
    return f"{x:.1f}".replace(".", ",")


def build_findings(r: dict[str, pd.DataFrame]) -> list[tuple[str, str]]:
    f: list[tuple[str, str]] = []
    p = r["param"].iloc[0]
    ref, debut = int(p.annee_ref), int(p.annee_debut) if pd.notna(p.annee_debut) else None

    # 1. Price vs volume adjustment
    idx = r["a09_indices"]
    if len(idx) >= 2:
        last = idx.iloc[-1]
        dv, dp = last.indice_volume - 100, last.indice_prix - 100
        if dv < -10 and dp > -5:
            lecture = ("le marché s'est ajusté par les **volumes**, pas par les prix : "
                       "les vendeurs ont préféré attendre plutôt que baisser")
        elif dp < -5:
            lecture = "les **prix** ont réellement corrigé"
        elif abs(dv) <= 10 and dp > 5:
            lecture = ("les **prix** ont progressé à volume quasi constant, "
                       "signe que la demande a absorbé la hausse")
        elif dv > 10 and dp > 0:
            lecture = "le marché est en **expansion** : plus de ventes et des prix en hausse"
        else:
            lecture = "le marché est resté globalement **stable**"
        f.append(("Prix contre volumes",
                  (f"Entre {debut} et {ref}, le nombre de ventes a évolué de {_pct(dv)} et le prix "
                  f"médian au m² de {_pct(dp)}. En clair, {lecture}.")))

    # 2. Peak year
    a = r["a01_marche_annuel"]
    full = a[a.annee_complete]
    if len(full) >= 2:
        pic = full.loc[full.ventes.idxmax()]
        dernier = full.iloc[-1]
        if int(pic.annee) != int(dernier.annee):
            f.append(("Le pic est passé",
                      (f"Le pic d'activité date de {int(pic.annee)} avec {_n(pic.ventes)} ventes. "
                      f"En {int(dernier.annee)}, on en compte {_n(dernier.ventes)}, soit "
                      f"{_pct(100 * (dernier.ventes / pic.ventes - 1))} par rapport au pic.")))

    # 3. Commune spread
    c = r["a03_communes"]
    if len(c) >= 2:
        top, bas = c.iloc[0], c.iloc[-1]
        f.append(("Un département, deux marchés",
                  f"En {ref}, {top.nom_commune} est la commune la plus chère "
                  f"({_n(top.prix_m2_median, ' €/m²')}) et {bas.nom_commune} la plus accessible "
                  f"({_n(bas.prix_m2_median, ' €/m²')}), un écart de "
                  f"x{top.prix_m2_median / bas.prix_m2_median:.1f}".replace(".", ",") +
                  f" (communes avec au moins {config.MIN_VENTES_COMMUNE} ventes)."))
        hausse = c.dropna(subset=["prix_m2_evol_pct"])
        hausse = hausse[hausse.ventes >= 2 * config.MIN_VENTES_COMMUNE]
        if not hausse.empty:
            h = hausse.loc[hausse.prix_m2_evol_pct.idxmax()]
            f.append(("Commune à surveiller",
                      (f"Parmi les communes avec au moins {2 * config.MIN_VENTES_COMMUNE} ventes, "
                      f"{h.nom_commune} affiche la plus forte hausse sur un an "
                      f"({_pct(h.prix_m2_evol_pct)}, à {_n(h.prix_m2_median, ' €/m²')}).")))

    # 4. Coastal premium
    lit = r["a06_prime_littorale"].dropna(subset=["prime_littorale_pct"])
    for row in lit.itertuples():
        if row.type_local == "Appartement":
            f.append(("Le prix de la mer",
                      (f"Un appartement sur une commune littorale se vend {_pct(row.prime_littorale_pct)} "
                      f"plus cher au m² que dans l'arrière-pays "
                      f"({_n(row.prix_m2_littoral, ' €')} contre {_n(row.prix_m2_arriere_pays, ' €')}).")))

    # 5. Small units premium
    t = r["a07_typologie"]
    if {"T1", "T4"} <= set(t.typologie):
        t1, t4 = t.set_index("typologie").loc["T1"], t.set_index("typologie").loc["T4"]
        f.append(("Les studios, chers au m²",
                  (f"Un T1 se négocie {_n(t1.prix_m2_median, ' €/m²')} contre "
                  f"{_n(t4.prix_m2_median, ' €/m²')} pour un T4 "
                  f"({_pct(100 * (t1.prix_m2_median / t4.prix_m2_median - 1))}). "
                  f"La demande locative et saisonnière tire les petites surfaces.")))

    # 6. Budget
    b = r["a08_budget"]
    if len(b) >= 2:
        f.append(("Ce que permet un budget de " + _n(config.BUDGET_REFERENCE_EUR, " €"),
                  (f"Au prix médian, {_n(config.BUDGET_REFERENCE_EUR, ' €')} achètent environ "
                  f"{_n(b.iloc[0].surface_pour_budget_m2, ' m²')} à {b.iloc[0].nom_commune} "
                  f"mais seulement {_n(b.iloc[-1].surface_pour_budget_m2, ' m²')} à {b.iloc[-1].nom_commune}.")))

    # 7. Seasonality
    s = r["a05_saisonnalite"].sort_values("part_annuelle_pct", ascending=False)
    if len(s) == 12:
        hauts = ", ".join(s.head(3).mois_libelle)
        f.append(("Saisonnalité",
                  (f"Les mois les plus actifs sont {hauts} ; {s.iloc[-1].mois_libelle} est le plus calme "
                  f"({_d(s.iloc[-1].part_annuelle_pct)} % des ventes annuelles contre "
                  f"{_d(s.iloc[0].part_annuelle_pct)} % pour {s.iloc[0].mois_libelle}).")))

    # 8. Data quality
    au = r["audit_nettoyage"]
    kept = au[au.etape == "99_conservee"]
    rej = au[au.etape != "99_conservee"]
    if not kept.empty and not rej.empty:
        main = rej.loc[rej.nb_mutations.idxmax()]
        f.append(("Qualité des données",
                  (f"{_n(au.nb_mutations.sum())} mutations brutes, {_n(kept.iloc[0].nb_mutations)} ventes "
                  f"de logements conservées ({_d(kept.iloc[0].pct)} %). Premier motif d'exclusion : "
                  f"« {main.etape[3:].replace('_', ' ')} » ({_d(main.pct)} %).")))
    return f


def build_model_findings(m) -> list[tuple[str, str]]:
    """Findings from the hedonic model (see model.py)."""
    f: list[tuple[str, str]] = []
    e = m.effects.set_index("niveau")
    if "T1" in e.index:
        f.append(("À caractéristiques égales",
                  f"Le modèle de prix (R² = {_d(m.r2 * 100)} %, {_n(m.n)} ventes) isole chaque facteur : "
                  f"un T1 vaut {_pct(e.loc['T1'].effet_pct)} au m² par rapport à un T3 de la même commune, "
                  f"la même année" +
                  (f", et une maison {_pct(e.loc['Maison'].effet_pct)} par rapport à un appartement(terrain compris)."
                   if "Maison" in e.index else ".")))
    c = m.communes
    if len(c) >= 3:
        g = c.loc[c.effet_composition_pts.abs().idxmax()]
        sens = "surestime" if g.effet_composition_pts > 0 else "sous-estime"
        f.append(("Le prix brut peut tromper",
                  f"À {g.nom_commune}, la médiane brute {sens} le niveau de prix de "
                  f"{_d(abs(g.effet_composition_pts))} points (indice {_d(g.indice_brut)} brut contre "
                  f"{_d(g.indice_ajuste)} à caractéristiques égales, {m.ref_commune} = 100) : "
                  f"c'est le type de biens vendus qui joue, pas la commune elle-même."))
    return f


def to_markdown(findings, demo: bool = False) -> str:
    lines = []
    if demo:
        lines.append("> ⚠️ **DONNÉES SYNTHÉTIQUES (mode démo)** : ces chiffres ne décrivent pas le marché réel.\n")
    for i, (titre, texte) in enumerate(findings, 1):
        lines.append(f"{i}. **{titre}.** {texte}")
    lines.append(f"\n_Généré automatiquement le {date.today():%d/%m/%Y} par `make run`._")
    return "\n".join(lines)


def write(findings, out_dir: Path, readme: Path | None = None, demo: bool = False) -> str:
    md = to_markdown(findings, demo)
    (out_dir / "FINDINGS.md").write_text("# Principaux enseignements\n\n" + md + "\n", encoding="utf-8")
    if readme is not None and readme.exists() and not demo:
        txt = readme.read_text(encoding="utf-8")
        txt = re.sub(r"(<!-- FINDINGS:START -->).*?(<!-- FINDINGS:END -->)",
                     lambda m: m.group(1) + "\n" + md + "\n" + m.group(2), txt, flags=re.DOTALL)
        readme.write_text(txt, encoding="utf-8")
    return md
