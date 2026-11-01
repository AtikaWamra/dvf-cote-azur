-- =====================================================================
-- 02_clean.sql : rebuild one row per sale, flag every rejected sale
-- with an explicit reason, and keep a full audit of the cleaning.
-- =====================================================================

-- Trap #1: a house with a garden appears on several lines (one per land
-- "culture"), with the same building surface repeated. Counting lines
-- would turn one house into three. We deduplicate dwellings first.
CREATE OR REPLACE TABLE int_logements AS
SELECT DISTINCT
    id_mutation,
    id_parcelle,
    COALESCE(lot1_numero, '')       AS lot1_numero,
    type_local,
    surface_reelle_bati,
    nombre_pieces_principales
FROM stg_dvf
WHERE type_local IN ('Maison', 'Appartement');

-- Land surface: one value per (parcel, culture), summed per sale.
CREATE OR REPLACE TABLE int_terrains AS
SELECT id_mutation, SUM(surface_terrain) AS surface_terrain
FROM (
    SELECT DISTINCT id_mutation, id_parcelle, nature_culture, surface_terrain
    FROM stg_dvf
    WHERE surface_terrain IS NOT NULL
)
GROUP BY id_mutation;

-- Sale-level grain
CREATE OR REPLACE TABLE int_mutations AS
WITH entete AS (
    SELECT
        id_mutation,
        ANY_VALUE(date_mutation)            AS date_mutation,
        ANY_VALUE(nature_mutation)          AS nature_mutation,
        -- Trap #2: the sale price is repeated on every line of the sale.
        -- It must never be summed.
        MAX(valeur_fonciere)                AS valeur_fonciere,
        ANY_VALUE(code_commune)             AS code_commune,
        ANY_VALUE(nom_commune)              AS nom_commune,
        ANY_VALUE(code_departement)         AS code_departement,
        COUNT(DISTINCT code_commune)        AS n_communes,
        COUNT(*) FILTER (WHERE type_local = 'Local industriel. commercial ou assimilé') AS n_locaux_pro,
        COUNT(*) FILTER (WHERE type_local = 'Dépendance') AS n_dependances,
        AVG(longitude)                      AS longitude,
        AVG(latitude)                       AS latitude
    FROM stg_dvf
    GROUP BY id_mutation
),
logements AS (
    SELECT
        id_mutation,
        COUNT(*)                            AS n_logements,
        MAX(type_local)                     AS type_local,
        MAX(surface_reelle_bati)            AS surface_bati,
        MAX(nombre_pieces_principales)      AS nb_pieces
    FROM int_logements
    GROUP BY id_mutation
)
SELECT
    e.*,
    COALESCE(l.n_logements, 0)              AS n_logements,
    l.type_local,
    l.surface_bati,
    l.nb_pieces,
    t.surface_terrain,
    e.valeur_fonciere / NULLIF(l.surface_bati, 0) AS prix_m2
FROM entete e
LEFT JOIN logements l USING (id_mutation)
LEFT JOIN int_terrains t USING (id_mutation);

-- Rule-based rejection, first matching reason wins (order = priority)
CREATE OR REPLACE TABLE int_mutations_flag AS
SELECT
    *,
    CASE
        WHEN nature_mutation <> 'Vente'                      THEN '01_pas_une_vente_simple'
        WHEN n_logements = 0                                 THEN '02_aucun_logement'
        WHEN n_logements > 1                                 THEN '03_vente_multi_logements'
        WHEN n_locaux_pro > 0                                THEN '04_vente_mixte_local_pro'
        WHEN n_communes > 1                                  THEN '05_vente_multi_communes'
        WHEN valeur_fonciere IS NULL OR surface_bati IS NULL THEN '06_prix_ou_surface_manquant'
        WHEN surface_bati < {{surface_min}} OR surface_bati > {{surface_max}} THEN '07_surface_hors_bornes'
        WHEN valeur_fonciere < {{valeur_min}} OR valeur_fonciere > {{valeur_max}} THEN '08_prix_hors_bornes'
        WHEN prix_m2 < {{prix_m2_min}} OR prix_m2 > {{prix_m2_max}} THEN '09_prix_m2_aberrant'
        ELSE NULL
    END AS motif_rejet
FROM int_mutations;

-- Statistical pass: trim the 1% tails per (type, year) on what survived
CREATE OR REPLACE TABLE int_mutations_flag AS
WITH bornes AS (
    SELECT type_local, YEAR(date_mutation) AS annee,
           QUANTILE_CONT(prix_m2, 0.01) AS p01,
           QUANTILE_CONT(prix_m2, 0.99) AS p99
    FROM int_mutations_flag
    WHERE motif_rejet IS NULL
    GROUP BY ALL
)
SELECT f.* REPLACE (
    CASE WHEN f.motif_rejet IS NULL AND (f.prix_m2 < b.p01 OR f.prix_m2 > b.p99)
         THEN '10_hors_p1_p99' ELSE f.motif_rejet END AS motif_rejet)
FROM int_mutations_flag f
LEFT JOIN bornes b
  ON f.type_local = b.type_local AND YEAR(f.date_mutation) = b.annee;

-- Cleaning audit: how many sales each rule removed (the "funnel")
CREATE OR REPLACE TABLE audit_nettoyage AS
SELECT
    COALESCE(motif_rejet, '99_conservee') AS etape,
    COUNT(*)                              AS nb_mutations,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS pct
FROM int_mutations_flag
GROUP BY 1
ORDER BY 1;
