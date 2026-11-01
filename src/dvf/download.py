"""Download Geo-DVF files (Etalab) for the configured départements and years."""
from __future__ import annotations

import logging
import urllib.error
import urllib.request
from pathlib import Path

from . import config

log = logging.getLogger(__name__)


def download(raw_dir: Path, departements=None, annees=None, force: bool = False) -> list[Path]:
    departements = departements or config.DEPARTEMENTS
    annees = annees or config.ANNEES
    raw_dir.mkdir(parents=True, exist_ok=True)
    fichiers = []
    for annee in annees:
        for dep in departements:
            cible = raw_dir / f"dvf_{dep}_{annee}.csv.gz"
            if cible.exists() and not force:
                log.info("Déjà présent : %s", cible.name)
                fichiers.append(cible)
                continue
            url = config.GEO_DVF_URL.format(annee=annee, dep=dep)
            try:
                log.info("Téléchargement %s", url)
                with urllib.request.urlopen(url, timeout=120) as r, open(cible, "wb") as f:
                    while chunk := r.read(1 << 20):
                        f.write(chunk)
                fichiers.append(cible)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    log.warning("Année %s non publiée pour le %s, ignorée.", annee, dep)
                    cible.unlink(missing_ok=True)
                else:
                    raise
    if not fichiers:
        raise RuntimeError("Aucun fichier DVF téléchargé. Vérifiez la connexion et config.ANNEES.")
    return fichiers
