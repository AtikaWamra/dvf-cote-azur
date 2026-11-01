"""Run the analysis queries and export result tables."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from . import config
from .pipeline import render

log = logging.getLogger(__name__)


def run_analyses(con, out_dir: Path) -> dict[str, pd.DataFrame]:
    tables_dir = out_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    adir = config.SQL_DIR / "analysis"
    con.execute(render((adir / "00_params.sql").read_text(encoding="utf-8")))
    results = {}
    for path in sorted(adir.glob("a*.sql")):
        name = path.stem
        df = con.execute(render(path.read_text(encoding="utf-8"))).df()
        df.to_csv(tables_dir / f"{name}.csv", index=False)
        results[name] = df
        log.info("  %-24s %5d lignes", name, len(df))
    results["audit_nettoyage"] = con.execute("SELECT * FROM audit_nettoyage").df()
    results["audit_nettoyage"].to_csv(tables_dir / "audit_nettoyage.csv", index=False)
    results["param"] = con.execute("SELECT * FROM param").df()
    return results


def export_powerbi(con, out_dir: Path) -> None:
    """Export the star schema for Power BI (Parquet is faster; CSV for portability)."""
    pbi = out_dir / "powerbi"
    pbi.mkdir(parents=True, exist_ok=True)
    for t in ["fact_ventes", "dim_date", "dim_commune", "dim_type_bien", "audit_nettoyage"]:
        con.execute(f"COPY {t} TO '{(pbi / (t + '.parquet')).as_posix()}' (FORMAT PARQUET)")
        con.execute(f"COPY {t} TO '{(pbi / (t + '.csv')).as_posix()}' (HEADER, DELIMITER ',')")
    log.info("Modèle exporté pour Power BI dans %s", pbi)


def export_tableau(con, out_dir: Path, extra: dict[str, pd.DataFrame] | None = None) -> None:
    """Export flat extracts for Tableau Public (text files only, one wide table)."""
    tab = out_dir / "tableau"
    tab.mkdir(parents=True, exist_ok=True)
    con.execute(render((config.SQL_DIR / "05_bi_extracts.sql").read_text(encoding="utf-8")))
    con.execute(f"COPY tableau_ventes TO '{(tab / 'tableau_ventes.csv').as_posix()}' (HEADER, DELIMITER ',')")
    for name, df in (extra or {}).items():
        df.to_csv(tab / f"{name}.csv", index=False, encoding="utf-8")
    log.info("Extraits Tableau exportés dans %s", tab)
