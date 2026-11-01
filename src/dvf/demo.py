"""Synthetic data in the exact Geo-DVF format, for tests, CI and offline demos.

It reproduces the real traps of DVF (multi-line sales, repeated prices,
gardens split by culture, mixed sales, outliers) so the cleaning logic is
tested on what actually goes wrong. The numbers are NOT market data.
"""
from __future__ import annotations

import csv
import gzip
import random
from datetime import date, timedelta
from pathlib import Path

COLUMNS = [
    "id_mutation", "date_mutation", "numero_disposition", "nature_mutation", "valeur_fonciere",
    "adresse_numero", "adresse_nom_voie", "code_postal", "code_commune", "nom_commune",
    "code_departement", "id_parcelle", "lot1_numero", "lot1_surface_carrez", "nombre_lots",
    "code_type_local", "type_local", "surface_reelle_bati", "nombre_pieces_principales",
    "code_nature_culture", "nature_culture", "surface_terrain", "longitude", "latitude",
]

# code, name, synthetic base €/m², weight, lat, lon
COMMUNES = [
    ("06088", "Nice", 5200, 30, 43.703, 7.266), ("06029", "Cannes", 6400, 10, 43.552, 7.017),
    ("06004", "Antibes", 5600, 9, 43.580, 7.123), ("06083", "Menton", 5000, 4, 43.775, 7.497),
    ("06027", "Cagnes-sur-Mer", 4600, 6, 43.664, 7.149), ("06069", "Grasse", 3200, 5, 43.658, 6.923),
    ("06155", "Vallauris", 4500, 3, 43.578, 7.054), ("06079", "Mandelieu-la-Napoule", 5000, 3, 43.546, 6.938),
    ("06123", "Saint-Laurent-du-Var", 4300, 3, 43.673, 7.190), ("06161", "Villeneuve-Loubet", 4800, 2, 43.659, 7.122),
    ("06085", "Mougins", 6000, 2, 43.600, 6.995), ("06152", "Valbonne", 5300, 2, 43.641, 7.009),
    ("06030", "Le Cannet", 4700, 4, 43.577, 7.019), ("06149", "Vence", 4400, 2, 43.722, 7.112),
    ("06084", "Mouans-Sartoux", 4500, 1, 43.620, 6.971), ("06121", "Saint-Jean-Cap-Ferrat", 14000, 0.4, 43.684, 7.330),
    ("06104", "Roquebrune-Cap-Martin", 6200, 1, 43.760, 7.461), ("06032", "Cap-d'Ail", 7500, 0.6, 43.721, 7.405),
    ("06012", "Biot", 4900, 1, 43.628, 7.096), ("06048", "Carros", 3000, 1, 43.788, 7.186),
]
YEAR_VOLUME = {2020: 0.85, 2021: 1.15, 2022: 1.10, 2023: 0.88, 2024: 0.80, 2025: 0.86, 2026: 0.88}
YEAR_PRICE = {2020: 1.00, 2021: 1.05, 2022: 1.11, 2023: 1.13, 2024: 1.11, 2025: 1.12, 2026: 1.13}
MONTH_W = [0.75, 0.8, 0.95, 0.95, 1.0, 1.15, 1.25, 0.85, 1.0, 1.05, 1.05, 1.2]


def _row(**kw):
    r = {c: "" for c in COLUMNS}
    r.update({k: ("" if v is None else v) for k, v in kw.items()})
    return r


def generate(out_dir: Path, n_per_year: int = 12000, years=(2020, 2021, 2022, 2023, 2024, 2025, 2026),
             seed: int = 42) -> list[Path]:
    rnd = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    weights = [c[3] for c in COMMUNES]
    paths = []
    for y in years:
        rows = []
        last_month = 6 if y == max(years) else 12  # current year is partial, like Geo-DVF
        n = int(n_per_year * YEAR_VOLUME.get(y, 1) * last_month / 12)
        for i in range(n):
            code, nom, base, _, lat, lon = rnd.choices(COMMUNES, weights)[0]
            m = rnd.choices(range(1, last_month + 1), MONTH_W[:last_month])[0]
            d = date(y, m, 1) + timedelta(days=rnd.randrange(27))
            mid = f"{y}-{i:06d}"
            parcelle = f"{code}000AB{rnd.randrange(9999):04d}"
            common = {"id_mutation": mid, "date_mutation": d.isoformat(), "numero_disposition": "000001",
                          "code_commune": code, "nom_commune": nom, "code_departement": "06",
                          "code_postal": "06000", "id_parcelle": parcelle,
                          "latitude": round(lat + rnd.gauss(0, 0.01), 6),
                          "longitude": round(lon + rnd.gauss(0, 0.01), 6)}
            kind = rnd.random()
            is_apt = rnd.random() < 0.72
            pieces = rnd.choices([1, 2, 3, 4, 5, 6], [18, 30, 27, 15, 7, 3])[0] if is_apt else rnd.choice([3, 4, 5, 6])
            surface = max(12, round((pieces * 22 + rnd.gauss(0, 9)) * (1 if is_apt else 1.4)))
            size_premium = {1: 1.18, 2: 1.06, 3: 1.0, 4: 0.96, 5: 0.94, 6: 0.92}[min(pieces, 6)]
            pm2 = base * YEAR_PRICE[y] * size_premium * (1.1 if not is_apt else 1) * rnd.lognormvariate(0, 0.22)
            price = round(surface * pm2, -2)
            nature = "Vente"
            if kind < 0.03:
                nature = rnd.choice(["Echange", "Vente en l'état futur d'achèvement", "Adjudication"])
            if kind < 0.15:  # dependency-only sale (parking, cellar)
                rows.append(_row(**common, nature_mutation=nature, valeur_fonciere=rnd.randrange(8, 60) * 1000,
                                 code_type_local="3", type_local="Dépendance", lot1_numero="12"))
                continue
            if kind < 0.24:  # bare land
                rows.append(_row(**common, nature_mutation=nature,
                                 valeur_fonciere=rnd.randrange(50, 600) * 1000,
                                 code_nature_culture="S", nature_culture="sols",
                                 surface_terrain=rnd.randrange(300, 3000)))
                continue
            if kind < 0.27:  # commercial premises
                rows.append(_row(**common, nature_mutation=nature, valeur_fonciere=price,
                                 code_type_local="4", type_local="Local industriel. commercial ou assimilé",
                                 surface_reelle_bati=surface))
                continue
            typ = "Appartement" if is_apt else "Maison"
            ctl = "2" if is_apt else "1"
            local = {"code_type_local": ctl, "type_local": typ, "surface_reelle_bati": surface,
                         "nombre_pieces_principales": pieces, "lot1_numero": "5" if is_apt else ""}
            if rnd.random() < 0.004:  # gross typo in price: outlier
                price = rnd.choice([1, 150, 99_000_000])
            if kind < 0.30 and kind >= 0.27:  # multi-dwelling block sale
                for k in range(rnd.randrange(2, 6)):
                    rows.append(_row(**common, nature_mutation=nature, valeur_fonciere=price * 3,
                                     **{**local, "lot1_numero": str(10 + k)}))
                continue
            if is_apt:
                rows.append(_row(**common, nature_mutation=nature, valeur_fonciere=price, **local))
                if rnd.random() < 0.35:
                    rows.append(_row(**common, nature_mutation=nature, valeur_fonciere=price,
                                     code_type_local="3", type_local="Dépendance", lot1_numero="40"))
            else:  # house: one line per land culture, building surface repeated
                for cult, lab in rnd.sample([("S", "sols"), ("AG", "terrains d'agrément"), ("J", "jardins")],
                                            rnd.randrange(1, 4)):
                    rows.append(_row(**common, nature_mutation=nature, valeur_fonciere=price, **local,
                                     code_nature_culture=cult, nature_culture=lab,
                                     surface_terrain=rnd.randrange(80, 900)))
        p = out_dir / f"dvf_06_{y}.csv.gz"
        with gzip.open(p, "wt", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
        paths.append(p)
    return paths
