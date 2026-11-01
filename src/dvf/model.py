"""Hedonic price model: what drives the price per m², all else being equal?

A median comparison mixes two things: the commune itself and what is sold
there. A commune selling mostly studios looks expensive per m² even if a
given flat costs the same as elsewhere. The model separates the two:

    log(prix_m2) = commune + type de bien + typologie + année
                   + dépendance + erreur

Land surface is deliberately left out: almost every house has land and, in
DVF, apartments carry the co-ownership plot, so it would duplicate the
house/apartment variable (perfect collinearity).

exp(coef) - 1 reads as "% de prix au m² en plus, toutes choses égales par
ailleurs". Standard errors are heteroskedasticity-robust (HC1).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from . import config

log = logging.getLogger(__name__)

AUTRES = "Autres communes"
REF_TYPO = "T3"
REF_TYPE = "Appartement"


@dataclass
class ModelResult:
    effects: pd.DataFrame       # non-commune effects, in %
    communes: pd.DataFrame      # raw vs adjusted commune index
    r2: float
    n: int
    ref_commune: str
    ref_annee: int


def _load(con) -> pd.DataFrame:
    return con.execute("""
        SELECT f.prix_m2, f.typologie, t.type_local, d.annee,
               f.avec_dependance::INT AS avec_dependance,
               c.nom_commune, c.est_littorale
        FROM fact_ventes f
        JOIN dim_date d USING (date_key)
        JOIN dim_commune c USING (code_commune)
        JOIN dim_type_bien t USING (type_bien_key)
        WHERE f.typologie <> 'Non renseigné'
          AND d.annee <= (SELECT annee_ref FROM param)
    """).df()


def fit(con) -> ModelResult:
    df = _load(con)
    counts = df.nom_commune.value_counts()
    keep = counts[counts >= config.MIN_VENTES_COMMUNE].index
    df["commune"] = df.nom_commune.where(df.nom_commune.isin(keep), AUTRES)
    ref_commune = counts.index[0]                     # most liquid market = reference
    ref_annee = int(df.annee.min())
    df["log_prix_m2"] = np.log(df.prix_m2)

    formula = (f"log_prix_m2 ~ C(commune, Treatment({ref_commune!r}))"
               f" + C(type_local, Treatment({REF_TYPE!r}))"
               f" + C(typologie, Treatment({REF_TYPO!r}))"
               f" + C(annee, Treatment({ref_annee}))"
               " + avec_dependance")
    res = smf.ols(formula, data=df).fit(cov_type="HC1")
    if np.linalg.matrix_rank(res.model.exog) < res.model.exog.shape[1]:
        raise ValueError("Modèle hédonique : variables colinéaires, coefficients non identifiables.")
    log.info("  Modèle hédonique : n=%d, R²=%.3f", int(res.nobs), res.rsquared)

    ci = res.conf_int()
    rows = []
    for name, coef in res.params.items():
        if name == "Intercept":
            continue
        if name.startswith("C(commune"):
            groupe = "Commune"
        elif name.startswith("C(type_local"):
            groupe = "Type de bien"
        elif name.startswith("C(typologie"):
            groupe = "Typologie"
        elif name.startswith("C(annee"):
            groupe = "Année"
        else:
            groupe = "Caractéristique"
        niveau = name.split("[T.")[-1].rstrip("]") if "[T." in name else name
        niveau = {"avec_dependance": "Avec dépendance"}.get(niveau, niveau)
        rows.append(dict(groupe=groupe, niveau=niveau,
                         effet_pct=100 * (np.exp(coef) - 1),
                         ic_bas_pct=100 * (np.exp(ci.loc[name, 0]) - 1),
                         ic_haut_pct=100 * (np.exp(ci.loc[name, 1]) - 1),
                         p_value=res.pvalues[name]))
    eff = pd.DataFrame(rows)

    # Raw vs adjusted commune index (reference commune = 100)
    raw = df.groupby("commune").agg(ventes=("prix_m2", "size"), prix_m2_median=("prix_m2", "median"),
                                    est_littorale=("est_littorale", "first"))
    raw = raw.drop(index=AUTRES, errors="ignore")
    raw["indice_brut"] = 100 * raw.prix_m2_median / raw.loc[ref_commune, "prix_m2_median"]
    adj = eff[eff.groupe == "Commune"].set_index("niveau").effet_pct
    raw["indice_ajuste"] = 100 + adj.reindex(raw.index).fillna(0)
    raw["effet_composition_pts"] = raw.indice_brut - raw.indice_ajuste
    raw = raw.reset_index().rename(columns={"commune": "nom_commune"})
    raw = raw.sort_values("indice_ajuste", ascending=False)
    raw["rang_brut"] = raw.indice_brut.rank(ascending=False, method="min").astype(int)
    raw["rang_ajuste"] = raw.indice_ajuste.rank(ascending=False, method="min").astype(int)

    return ModelResult(effects=eff[eff.groupe != "Commune"].reset_index(drop=True),
                       communes=raw.reset_index(drop=True),
                       r2=float(res.rsquared), n=int(res.nobs),
                       ref_commune=ref_commune, ref_annee=ref_annee)


def save(m: ModelResult, out_dir: Path) -> None:
    t = out_dir / "tables"
    t.mkdir(parents=True, exist_ok=True)
    m.effects.round(3).to_csv(t / "m01_effets_prix.csv", index=False)
    m.communes.round(2).to_csv(t / "m02_communes_ajustees.csv", index=False)
    (t / "m00_modele.txt").write_text(
        f"Modèle hédonique OLS (erreurs robustes HC1)\nObservations : {m.n}\nR² : {m.r2:.3f}\n"
        f"Références : commune = {m.ref_commune}, type = {REF_TYPE}, typologie = {REF_TYPO}, "
        f"année = {m.ref_annee}\n", encoding="utf-8")
