"""Tests on a hand-built fixture where the correct answer is known for every sale.

Each sale reproduces one real DVF trap. If a cleaning rule regresses,
the exact test that names the trap fails.
"""
import csv
import gzip

import pandas as pd
import pytest

from dvf import analysis, cli, config, demo, model, pipeline
from dvf.demo import COLUMNS


def row(mid, **kw):
    base = {"id_mutation": mid, "date_mutation": "2024-05-15", "nature_mutation": "Vente",
                "code_commune": "06088", "nom_commune": "Nice", "code_departement": "06",
                "id_parcelle": f"06088000AB{mid[-2:]}", "latitude": "43.70", "longitude": "7.26"}
    base.update(kw)
    return {c: base.get(c, "") for c in COLUMNS}


APT = {"type_local": "Appartement", "code_type_local": "2", "nombre_pieces_principales": "3"}
FIXTURE = [
    # M01 simple apartment: kept, 300 000 / 60 = 5 000 €/m²
    row("M01", valeur_fonciere="300000", surface_reelle_bati="60", **APT),
    # M02 house on 3 land-culture lines, same building surface repeated: ONE house
    *[row("M02", valeur_fonciere="600000", type_local="Maison", code_type_local="1",
          surface_reelle_bati="120", nombre_pieces_principales="5",
          nature_culture=c, surface_terrain=s)
      for c, s in [("sols", "100"), ("jardins", "200"), ("terrains d'agrément", "300")]],
    # M03 apartment + cellar: kept, flagged with a dependency
    row("M03", valeur_fonciere="250000", surface_reelle_bati="50", **APT),
    row("M03", valeur_fonciere="250000", type_local="Dépendance", code_type_local="3", lot1_numero="40"),
    # M04 two apartments sold together: price per m² is meaningless
    row("M04", valeur_fonciere="500000", surface_reelle_bati="40", lot1_numero="1", **APT),
    row("M04", valeur_fonciere="500000", surface_reelle_bati="45", lot1_numero="2", **APT),
    # M05 exchange, not a sale
    row("M05", nature_mutation="Echange", valeur_fonciere="300000", surface_reelle_bati="60", **APT),
    # M06 parking only
    row("M06", valeur_fonciere="25000", type_local="Dépendance", code_type_local="3"),
    # M07 apartment sold with a shop
    row("M07", valeur_fonciere="400000", surface_reelle_bati="60", **APT),
    row("M07", valeur_fonciere="400000", surface_reelle_bati="30",
        type_local="Local industriel. commercial ou assimilé", code_type_local="4"),
    # M08 5 m² "apartment"
    row("M08", valeur_fonciere="60000", surface_reelle_bati="5", **APT),
    # M09 1 € symbolic sale
    row("M09", valeur_fonciere="1", surface_reelle_bati="60", **APT),
    # M10 5 M€ for 50 m² = 100 000 €/m²
    row("M10", valeur_fonciere="5000000", surface_reelle_bati="50", **APT),
]
EXPECTED = {
    "M01": None, "M02": None, "M03": None,
    "M04": "03_vente_multi_logements", "M05": "01_pas_une_vente_simple",
    "M06": "02_aucun_logement", "M07": "04_vente_mixte_local_pro",
    "M08": "07_surface_hors_bornes", "M09": "08_prix_hors_bornes", "M10": "09_prix_m2_aberrant",
}


@pytest.fixture(scope="module")
def con(tmp_path_factory):
    raw = tmp_path_factory.mktemp("raw")
    with gzip.open(raw / "dvf_06_2024.csv.gz", "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(FIXTURE)
    return pipeline.build(raw, tmp_path_factory.mktemp("db") / "test.duckdb")


@pytest.mark.parametrize("mid,motif", EXPECTED.items())
def test_each_trap_gets_the_right_rejection_reason(con, mid, motif):
    got = con.execute("SELECT motif_rejet FROM int_mutations_flag WHERE id_mutation = ?", [mid]).fetchone()
    assert got is not None, f"{mid} disparu du pipeline"
    assert got[0] == motif


def test_house_split_on_culture_lines_is_one_dwelling(con):
    n, surf, terrain, pm2 = con.execute(
        "SELECT n_logements, surface_bati, surface_terrain, prix_m2 FROM int_mutations WHERE id_mutation='M02'"
    ).fetchone()
    assert n == 1
    assert surf == 120
    assert terrain == 600          # 100 + 200 + 300, land is summed
    assert pm2 == 5000             # price NOT multiplied by the 3 lines


def test_price_is_never_summed_across_lines(con):
    v = con.execute("SELECT valeur_fonciere FROM fact_ventes WHERE id_mutation='M03'").fetchone()[0]
    assert v == 250000


def test_dependency_flag(con):
    flags = dict(con.execute("SELECT id_mutation, avec_dependance FROM fact_ventes").fetchall())
    assert flags == {"M01": False, "M02": False, "M03": True}


def test_fact_contains_exactly_the_clean_sales(con):
    ids = {r[0] for r in con.execute("SELECT id_mutation FROM fact_ventes").fetchall()}
    assert ids == {k for k, v in EXPECTED.items() if v is None}


def test_typologie_buckets(con):
    t = dict(con.execute("SELECT id_mutation, typologie FROM fact_ventes").fetchall())
    assert t["M01"] == "T3" and t["M02"] == "T5+"


def test_coastal_flag_from_seed(con):
    assert con.execute("SELECT est_littorale FROM dim_commune WHERE code_commune='06088'").fetchone()[0]


def test_all_blocking_quality_checks_pass(con):
    q = pipeline.run_quality_checks(con)
    assert q.ok, q.blocking_failures.to_string()


def test_render_rejects_unknown_placeholder():
    with pytest.raises(ValueError):
        pipeline.render("SELECT {{nope}}")


def test_end_to_end_on_synthetic_data(tmp_path):
    raw = tmp_path / "raw"
    demo.generate(raw, n_per_year=1500, years=(2022, 2023, 2024, 2025))
    assert cli.run(raw, tmp_path / "out", tmp_path / "img", is_demo=True) == 0
    assert (tmp_path / "out" / "FINDINGS.md").read_text(encoding="utf-8").count("**") >= 10
    assert len(list((tmp_path / "img").glob("*.png"))) == 11
    out = tmp_path / "out"
    assert (out / "powerbi" / "fact_ventes.parquet").exists()
    assert (out / "note_de_synthese.pdf").stat().st_size > 50_000


def test_tableau_extract_is_one_row_per_sale(tmp_path):
    raw = tmp_path / "raw"
    demo.generate(raw, n_per_year=800, years=(2023, 2024))
    con = pipeline.build(raw, tmp_path / "t.duckdb")
    analysis.export_tableau(con, tmp_path)
    tab = pd.read_csv(tmp_path / "tableau" / "tableau_ventes.csv")
    assert len(tab) == con.execute("SELECT COUNT(*) FROM fact_ventes").fetchone()[0]
    assert tab["Id Vente"].is_unique
    assert set(tab["Zone"]) <= {"Littoral", "Arrière-pays"}


@pytest.fixture(scope="module")
def fitted_model(tmp_path_factory):
    raw = tmp_path_factory.mktemp("raw_model")
    demo.generate(raw, n_per_year=6000, years=(2020, 2021, 2022, 2023))
    con = pipeline.build(raw, tmp_path_factory.mktemp("dbm") / "m.duckdb")
    con.execute(pipeline.render((config.SQL_DIR / "analysis" / "00_params.sql").read_text(encoding="utf-8")))
    return model.fit(con)


@pytest.mark.parametrize("niveau,attendu", [
    ("T1", 18.0),    # demo.py: size premium 1.18 vs T3
    ("T2", 6.0),     # 1.06
    ("T4", -4.0),    # 0.96
    ("2022", 11.0),  # YEAR_PRICE 1.11 vs 2020
])
def test_model_recovers_planted_effects(fitted_model, niveau, attendu):
    """The synthetic generator plants known effects: the model must find them."""
    e = fitted_model.effects.set_index("niveau").effet_pct
    assert e[niveau] == pytest.approx(attendu, abs=2.5)


def test_model_reference_commune_is_100(fitted_model):
    c = fitted_model.communes.set_index("nom_commune")
    assert c.loc[fitted_model.ref_commune, "indice_ajuste"] == 100
    assert c.loc[fitted_model.ref_commune, "indice_brut"] == pytest.approx(100)
