"""Project configuration. Edit DEPARTEMENTS / ANNEES to change the scope."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
SEEDS_DIR = ROOT / "seeds"

# Scope: Alpes-Maritimes by default. Add "83" for the Var.
DEPARTEMENTS = ["06"]
# Geo-DVF publishes the last ~5 complete years plus the current one.
# Years that are not published are skipped by the downloader.
ANNEES = [2020, 2021, 2022, 2023, 2024, 2025, 2026]

GEO_DVF_URL = "https://files.data.gouv.fr/geo-dvf/latest/csv/{annee}/departements/{dep}.csv.gz"

DEPARTEMENT_NOMS = {"06": "Alpes-Maritimes", "83": "Var"}

# Cleaning rules (documented in docs/methodologie.md)
SURFACE_MIN_M2 = 9          # legal minimum for a dwelling (loi Carrez / décence)
SURFACE_MAX_M2 = 1000
VALEUR_MIN_EUR = 15_000
VALEUR_MAX_EUR = 50_000_000
PRIX_M2_MIN = 500
PRIX_M2_MAX = 40_000
MIN_VENTES_COMMUNE = 30     # below this, a commune median is not reported

# Communes compared side by side in the dashboard and the report
COMMUNES_FOCUS = ["Antibes", "Nice", "Cannes", "Menton", "Cagnes-sur-Mer", "Grasse"]

# Budget used in the "what does it buy" analysis
BUDGET_REFERENCE_EUR = 300_000
