"""Command line entry point.

    python -m dvf.cli download     # fetch Geo-DVF files
    python -m dvf.cli run          # build warehouse + quality gate + analyses + charts + findings
    python -m dvf.cli all          # download then run
    python -m dvf.cli demo         # same pipeline on synthetic data (no internet needed)
"""
from __future__ import annotations

import argparse
import logging
import sys
import time

from . import analysis, charts, config, demo, download, insights, model, pipeline, report

log = logging.getLogger("dvf")


def run(raw_dir, out_dir, img_dir, is_demo=False) -> int:
    t0 = time.perf_counter()
    db = out_dir / "dvf.duckdb"
    con = pipeline.build(raw_dir, db)

    log.info("Contrôles qualité")
    q = pipeline.run_quality_checks(con)
    (out_dir / "quality_report.md").write_text(
        "# Rapport qualité\n\n" + q.table.to_markdown(index=False) + "\n", encoding="utf-8")
    for row in q.table.itertuples():
        log.info("  [%-6s] %s (%d)", row.statut, row.controle, row.violations)
    if not q.ok:
        log.error("Contrôles bloquants en échec : arrêt avant publication des analyses.")
        return 1

    log.info("Analyses")
    results = analysis.run_analyses(con, out_dir)

    log.info("Modèle de prix")
    m = model.fit(con)
    model.save(m, out_dir)

    log.info("Exports BI")
    analysis.export_powerbi(con, out_dir)
    coords = con.execute("SELECT nom_commune, latitude, longitude FROM dim_commune").df()
    analysis.export_tableau(con, out_dir, extra={
        "tableau_communes": m.communes.merge(coords, on="nom_commune", how="left").round(2),
        "tableau_moteurs_prix": m.effects.round(2),
        "tableau_audit": results["audit_nettoyage"],
    })

    log.info("Graphiques")
    charts.make_all(con, results, img_dir, m)

    log.info("Enseignements")
    findings = insights.build_findings(results) + insights.build_model_findings(m)
    md = insights.write(findings, out_dir, readme=config.ROOT / "README.md", demo=is_demo)
    print("\n" + md + "\n")

    log.info("Note de synthèse")
    pdf = report.build(results, findings, img_dir, out_dir / "note_de_synthese.pdf", demo=is_demo)
    log.info("  %s", pdf.name)
    n = con.execute("SELECT COUNT(*) FROM fact_ventes").fetchone()[0]
    log.info("Terminé : %s ventes modélisées en %.1fs", f"{n:,}".replace(",", " "), time.perf_counter() - t0)
    return 0


def main(argv=None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser(prog="dvf")
    ap.add_argument("command", choices=["download", "run", "all", "demo"])
    ap.add_argument("--force", action="store_true", help="re-download existing files")
    a = ap.parse_args(argv)

    raw = config.ROOT / "data" / "raw"
    if a.command in ("download", "all"):
        download.download(raw, force=a.force)
    if a.command in ("run", "all"):
        return run(raw, config.ROOT / "outputs", config.ROOT / "images")
    if a.command == "demo":
        demo_raw = config.ROOT / "data" / "demo"
        demo.generate(demo_raw)
        return run(demo_raw, config.ROOT / "outputs_demo", config.ROOT / "outputs_demo" / "images",
                   is_demo=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
