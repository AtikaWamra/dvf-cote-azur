# Marché immobilier de la Côte d'Azur : où et quand acheter ?

![CI](https://github.com/AtikaWamra/dvf-cote-azur/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.10+-2a78d6)
![DuckDB](https://img.shields.io/badge/SQL-DuckDB-2a78d6)
![Power BI](https://img.shields.io/badge/Power%20BI-dashboard-eb6834)
![Tableau](https://img.shields.io/badge/Tableau-Public-eb6834)
![Actualisation](https://github.com/AtikaWamra/dvf-cote-azur/actions/workflows/refresh.yml/badge.svg)

Analyse de **toutes les ventes immobilières des Alpes-Maritimes** depuis 2020, à partir des données notariales ouvertes (DVF). Du fichier brut à un tableau de bord **Power BI** et une histoire de données **Tableau Public**, avec un pipeline SQL testé, des contrôles qualité automatiques, un modèle statistique des prix et une note de synthèse PDF. Le tout se met à jour seul chaque mois.

**[Tableau de bord Power BI](#)** · **[Story Tableau Public](#)** · **[Note de synthèse (PDF)](outputs/note_de_synthese.pdf)** · [Méthodologie](docs/methodologie.md)

![Carte des prix](images/05_carte_prix.png)

---

## La question métier

> *Pour un acheteur ou un investisseur : quelles communes offrent le meilleur rapport prix/emplacement, comment le marché a-t-il réagi à la hausse des taux de 2023, et que peut-on acheter avec un budget donné ?*

## Principaux enseignements

<!-- FINDINGS:START -->
_Lancez `make all` pour générer les enseignements à partir des données réelles._
<!-- FINDINGS:END -->

## Deux outils, deux usages

**Power BI pour piloter, Tableau pour raconter.** Le même modèle de données alimente les deux.

| | Power BI | Tableau Public |
|---|---|---|
| Pour qui | un décideur, usage récurrent | grand public, lecture guidée |
| Format | tableau de bord 5 pages, KPI, simulateur | **Story** en 5 étapes |
| Données | schéma en étoile, mesures DAX | extrait plat, expressions **LOD** |
| Point fort | time intelligence, paramètre What-if | carte de **chaque vente**, bonnes affaires, viz in tooltip |

### Power BI

| Vue d'ensemble | Carte et communes | Simulateur de budget |
|---|---|---|
| ![](images/pbi_page1.png) | ![](images/pbi_page2.png) | ![](images/pbi_page4.png) |

5 pages : vue d'ensemble, carte et classement des communes, tendances, **simulateur de budget interactif** (curseur de 100 000 à 1 M€) et qualité des données. Mesures DAX : évolutions N-1, 12 mois glissants, classement dynamique, prime littorale, titres dynamiques. Voir [`powerbi/`](powerbi/).

### Tableau

| Carte des ventes | Bonnes affaires | Ce qui fait le prix |
|---|---|---|
| ![](images/tab_story3.png) | ![](images/tab_story_affaires.png) | ![](images/tab_story4.png) |

Story en 5 points sur Tableau Public. Expressions LOD (`FIXED` par commune, année et type pour situer chaque vente par rapport à son marché), calculs de table (N-1, 12 mois glissants, rang), paramètres (budget, mesure dynamique, seuil de bonne affaire), action d'ensemble pour comparer des communes, info-bulle contenant un graphique. Voir [`tableau/`](tableau/).

## Analyses

| | |
|---|---|
| ![](images/02_prix_vs_volumes.png) | ![](images/04_top_communes.png) |
| ![](images/06_prime_littorale.png) | ![](images/08_budget.png) |
| ![](images/07_typologies.png) | ![](images/09_villes_cles.png) |

## Ce qui fait le prix : un modèle statistique

Comparer des médianes mélange deux choses : la commune, et ce qui s'y vend. Une commune qui vend surtout des studios paraît chère au m² sans l'être. Un **modèle de régression hédonique** (OLS sur le log du prix au m², erreurs robustes) sépare les effets : commune, type de bien, typologie, année, dépendance.

| | |
|---|---|
| ![](images/10_moteurs_prix.png) | ![](images/11_prix_brut_vs_ajuste.png) |

Le modèle est validé par un test : sur des données synthétiques où les effets sont connus à l'avance, il doit les retrouver à ±2,5 points.

## Note de synthèse

Chaque exécution produit une [note de synthèse de 2 pages](outputs/note_de_synthese.pdf) pour un lecteur non technique : chiffres clés, enseignements, graphiques. Générée à partir des mêmes tables que le reste, elle ne peut pas se désynchroniser des données.

## Architecture

```mermaid
flowchart LR
    A[Geo-DVF<br/>data.gouv.fr] -->|download.py| B[(CSV bruts)]
    B -->|01_staging.sql| C[stg_dvf<br/>typage]
    C -->|02_clean.sql| D[int_mutations<br/>1 ligne = 1 vente<br/>+ motif de rejet]
    D -->|03_star_schema.sql| E[Schéma en étoile]
    E -->|04_quality_checks.sql| F{Contrôles<br/>qualité}
    F -->|OK| G[10 analyses SQL]
    F -->|échec bloquant| X[Arrêt]
    E --> M[Modèle de prix<br/>OLS hédonique]
    G --> H[11 graphiques]
    M --> H
    G --> I[Enseignements<br/>auto-générés]
    M --> I
    H --> P[Note de synthèse PDF]
    I --> P
    E --> J[Parquet] --> K[Power BI]
    E --> L[Extrait plat] --> T[Tableau Public]
```

## Modèle de données

```mermaid
erDiagram
    fact_ventes }o--|| dim_date : date_key
    fact_ventes }o--|| dim_commune : code_commune
    fact_ventes }o--|| dim_type_bien : type_bien_key
    fact_ventes {
        string id_mutation PK
        int date_key FK
        string code_commune FK
        int type_bien_key FK
        float valeur_fonciere
        float surface_bati
        string typologie
        float prix_m2
    }
    dim_commune {
        string code_commune PK
        string nom_commune
        bool est_littorale
        float latitude
        float longitude
    }
    dim_date {
        int date_key PK
        date date
        int annee
        string annee_mois
        string saison
    }
    dim_type_bien {
        int type_bien_key PK
        string type_local
    }
```

## Les pièges des données DVF, et comment je les ai traités

Les données DVF sont publiques mais **trompeuses si on les lit naïvement**. Ce projet en traite trois :

**1. Une ligne n'est pas une vente.** Une maison avec jardin apparaît sur trois lignes (une par nature de terrain), avec la surface et le prix répétés. Un `COUNT(*)` donne trois maisons ; un `SUM(valeur_fonciere)` triple le prix. Le pipeline dédoublonne les logements avant de compter, et prend le prix une seule fois par vente.

**2. Les ventes groupées faussent le prix au m².** Un immeuble de 5 appartements vendu en un seul acte affiche un prix global. Divisé par la surface d'un seul lot, il produit un prix au m² absurde. Ces ventes sont isolées et exclues.

**3. L'année en cours est incomplète.** Geo-DVF publie avec environ 6 mois de retard. Comparer l'année en cours à une année pleine affiche une fausse chute de 50 % des ventes. Les analyses se calent sur la dernière année complète.

Chaque vente exclue reçoit un **motif explicite**, et un contrôle bloquant vérifie qu'aucune vente ne disparaît en silence :

![Entonnoir de nettoyage](images/01_entonnoir_nettoyage.png)

## Qualité et tests

- **11 contrôles qualité automatiques** sur le modèle (unicité, intégrité référentielle, réconciliation brut/conservé/rejeté, continuité du calendrier, bornes métier). Un échec bloquant arrête le pipeline avant toute publication. Rapport : `outputs/quality_report.md`.
- **25 tests** (`pytest`) : un jeu de données construit à la main où chaque vente reproduit un piège réel, la validation du modèle sur des effets connus, et le pipeline de bout en bout.
- **Intégration continue** GitHub Actions : lint, tests et pipeline complet sur données synthétiques à chaque commit.
- **Actualisation automatique** : chaque mois, une GitHub Action retélécharge DVF, relance tout et publie le README, les graphiques et la note mis à jour. Si un contrôle bloquant échoue, rien n'est publié.

## Lancer le projet

```bash
git clone https://github.com/AtikaWamra/dvf-cote-azur.git
cd dvf-cote-azur
python -m venv .venv && source .venv/bin/activate   # Windows : .venv\Scripts\activate
make install
make all        # téléchargement + pipeline complet (environ 1 minute)
```

Sans `make` (Windows) : `pip install -e ".[dev]"` puis `python -m dvf.cli all`.

Sans connexion : `make demo` exécute tout le pipeline sur des données synthétiques au format DVF.

Pour ajouter le Var : `DEPARTEMENTS = ["06", "83"]` dans `src/dvf/config.py`.

## Structure

```
dvf-cote-azur/
├── sql/
│   ├── 01_staging.sql          typage des fichiers bruts
│   ├── 02_clean.sql            grain vente + motifs de rejet + audit
│   ├── 03_star_schema.sql      modèle en étoile
│   ├── 04_quality_checks.sql   contrôles qualité
│   ├── analysis/               10 requêtes d'analyse
│   └── 05_bi_extracts.sql      extrait plat pour Tableau
├── src/dvf/                    pipeline, modèle, graphiques, enseignements, note PDF
├── tests/                      pièges DVF, validation du modèle, bout en bout
├── powerbi/                    mesures DAX, thème, guide de construction
├── tableau/                    champs calculés et LOD, guide de la Story
├── .github/workflows/          CI + actualisation mensuelle
├── seeds/                      référentiels (communes littorales)
├── docs/                       méthodologie, dictionnaire de données
└── images/                     graphiques générés
```

## Stack

**SQL** (DuckDB : CTE, fonctions de fenêtre, `QUANTILE_CONT`, `FILTER`) · **Python** (pandas, statsmodels, matplotlib, reportlab) · **Power BI** (DAX, What-if, info-bulles) · **Tableau** (LOD, calculs de table, paramètres, actions d'ensemble) · **pytest** · **GitHub Actions**

## Source et licence

Données : [Demandes de valeurs foncières géolocalisées](https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/), DGFiP / Etalab, Licence Ouverte 2.0. Code : MIT.

---

**Atika Wamra** · Data Analyst · [LinkedIn](https://linkedin.com/in/wamra-atika) · [GitHub](https://github.com/AtikaWamra)
