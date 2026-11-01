-- =====================================================================
-- 03_star_schema.sql : analytics model (Kimball star schema)
--   fact_ventes  ->  dim_date, dim_commune, dim_type_bien
-- =====================================================================

-- dim_date: continuous calendar (required by Power BI time intelligence)
CREATE OR REPLACE TABLE dim_date AS
WITH bornes AS (
    SELECT DATE_TRUNC('year', MIN(date_mutation)) AS d0,
           DATE_TRUNC('year', MAX(date_mutation)) + INTERVAL 1 YEAR - INTERVAL 1 DAY AS d1
    FROM int_mutations_flag
)
SELECT
    CAST(STRFTIME(d, '%Y%m%d') AS INTEGER)       AS date_key,
    CAST(d AS DATE)                              AS date,
    YEAR(d)                                      AS annee,
    QUARTER(d)                                   AS trimestre,
    'T' || QUARTER(d) || ' ' || YEAR(d)          AS trimestre_libelle,
    MONTH(d)                                     AS mois,
    STRFTIME(d, '%Y-%m')                         AS annee_mois,
    CASE MONTH(d) WHEN 1 THEN 'janv.' WHEN 2 THEN 'févr.' WHEN 3 THEN 'mars'
        WHEN 4 THEN 'avr.' WHEN 5 THEN 'mai' WHEN 6 THEN 'juin' WHEN 7 THEN 'juil.'
        WHEN 8 THEN 'août' WHEN 9 THEN 'sept.' WHEN 10 THEN 'oct.' WHEN 11 THEN 'nov.'
        ELSE 'déc.' END                          AS mois_libelle,
    CASE WHEN MONTH(d) IN (6,7,8) THEN 'Été' WHEN MONTH(d) IN (9,10,11) THEN 'Automne'
         WHEN MONTH(d) IN (12,1,2) THEN 'Hiver' ELSE 'Printemps' END AS saison
FROM bornes, GENERATE_SERIES(d0, d1, INTERVAL 1 DAY) AS t(d);

-- dim_commune: latest official name, coastal flag from the seed file
CREATE OR REPLACE TABLE dim_commune AS
SELECT
    m.code_commune,
    ARG_MAX(m.nom_commune, m.date_mutation)      AS nom_commune,
    ANY_VALUE(m.code_departement)                AS code_departement,
    ANY_VALUE(d.nom_departement)                 AS nom_departement,
    BOOL_OR(l.code_commune IS NOT NULL)          AS est_littorale,
    MEDIAN(m.latitude)                           AS latitude,
    MEDIAN(m.longitude)                          AS longitude
FROM int_mutations_flag m
LEFT JOIN seed_communes_littorales l ON l.code_commune = m.code_commune
LEFT JOIN seed_departements d        ON d.code_departement = m.code_departement
WHERE m.motif_rejet IS NULL
GROUP BY m.code_commune;

-- dim_type_bien
CREATE OR REPLACE TABLE dim_type_bien AS
SELECT * FROM (VALUES (1, 'Appartement'), (2, 'Maison')) AS t(type_bien_key, type_local);

-- fact_ventes: one row per clean residential sale
CREATE OR REPLACE TABLE fact_ventes AS
SELECT
    m.id_mutation,
    CAST(STRFTIME(m.date_mutation, '%Y%m%d') AS INTEGER) AS date_key,
    m.code_commune,
    t.type_bien_key,
    m.valeur_fonciere,
    m.surface_bati,
    m.nb_pieces,
    CASE WHEN m.nb_pieces IS NULL OR m.nb_pieces = 0 THEN 'Non renseigné'
         WHEN m.nb_pieces >= 5 THEN 'T5+'
         ELSE 'T' || m.nb_pieces END                     AS typologie,
    COALESCE(m.surface_terrain, 0)                       AS surface_terrain,
    m.n_dependances > 0                                  AS avec_dependance,
    ROUND(m.prix_m2, 2)                                  AS prix_m2,
    m.latitude,
    m.longitude
FROM int_mutations_flag m
JOIN dim_type_bien t USING (type_local)
WHERE m.motif_rejet IS NULL;
