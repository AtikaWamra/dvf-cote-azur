"""Build the DuckDB warehouse: staging -> cleaning -> star schema -> quality gate."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path

import duckdb
import pandas as pd

from . import config

log = logging.getLogger(__name__)


def render(sql: str, **params) -> str:
    """Tiny templating: replaces {{name}} placeholders with config values."""
    defaults = {
        "surface_min": config.SURFACE_MIN_M2,
        "surface_max": config.SURFACE_MAX_M2,
        "valeur_min": config.VALEUR_MIN_EUR,
        "valeur_max": config.VALEUR_MAX_EUR,
        "prix_m2_min": config.PRIX_M2_MIN,
        "prix_m2_max": config.PRIX_M2_MAX,
        "min_ventes": config.MIN_VENTES_COMMUNE,
        "budget": config.BUDGET_REFERENCE_EUR,
        "communes_focus": ", ".join("'" + c.replace("'", "''") + "'" for c in config.COMMUNES_FOCUS),
    }
    defaults.update(params)
    for k, v in defaults.items():
        sql = sql.replace("{{" + k + "}}", str(v))
    if "{{" in sql:
        raise ValueError(f"Placeholder non résolu dans : {sql[sql.index('{{'):][:40]}")
    return sql


def run_sql_file(con, path: Path, **params):
    t0 = time.perf_counter()
    con.execute(render(path.read_text(encoding="utf-8"), **params))
    log.info("  %-28s %.2fs", path.name, time.perf_counter() - t0)


def load_seeds(con):
    con.execute(f"""CREATE OR REPLACE TABLE seed_communes_littorales AS
        SELECT * FROM read_csv('{(config.SEEDS_DIR / 'communes_littorales_06.csv').as_posix()}',
                               header=true, all_varchar=true)""")
    con.execute(f"""CREATE OR REPLACE TABLE seed_departements AS
        SELECT * FROM read_csv('{(config.SEEDS_DIR / 'departements.csv').as_posix()}',
                               header=true, all_varchar=true)""")


@dataclass
class QualityResult:
    table: pd.DataFrame

    @property
    def blocking_failures(self) -> pd.DataFrame:
        t = self.table
        return t[(t.severite == "bloquant") & (t.violations > 0)]

    @property
    def ok(self) -> bool:
        return self.blocking_failures.empty


def run_quality_checks(con) -> QualityResult:
    sql = render((config.SQL_DIR / "04_quality_checks.sql").read_text(encoding="utf-8"))
    df = con.execute(sql).df()
    df["statut"] = df.apply(
        lambda r: "OK" if r.violations == 0 else ("ÉCHEC" if r.severite == "bloquant" else "ALERTE"),
        axis=1,
    )
    return QualityResult(df)


def build(raw_dir: Path, db_path: Path) -> duckdb.DuckDBPyConnection:
    files = sorted(raw_dir.glob("*.csv*"))
    if not files:
        raise FileNotFoundError(f"Aucun fichier dans {raw_dir}. Lancez d'abord : make download")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db_path.unlink(missing_ok=True)
    con = duckdb.connect(str(db_path))
    log.info("Construction de l'entrepôt à partir de %d fichier(s)", len(files))
    load_seeds(con)
    raw_glob = (raw_dir / "*.csv*").as_posix()
    run_sql_file(con, config.SQL_DIR / "01_staging.sql", raw_glob=raw_glob)
    run_sql_file(con, config.SQL_DIR / "02_clean.sql")
    run_sql_file(con, config.SQL_DIR / "03_star_schema.sql")
    return con
