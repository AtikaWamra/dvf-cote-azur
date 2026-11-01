-- =====================================================================
-- 01_staging.sql : raw Geo-DVF files -> typed staging table
-- One row in Geo-DVF = one (mutation x parcel x local x culture) line,
-- NOT one sale. The sale-level grain is rebuilt in 02_clean.sql.
-- =====================================================================

CREATE OR REPLACE TABLE stg_dvf AS
SELECT
    id_mutation,
    CAST(date_mutation AS DATE)                 AS date_mutation,
    nature_mutation,
    TRY_CAST(valeur_fonciere AS DOUBLE)         AS valeur_fonciere,
    LPAD(CAST(code_commune AS VARCHAR), 5, '0') AS code_commune,
    nom_commune,
    LPAD(CAST(code_departement AS VARCHAR), 2, '0') AS code_departement,
    id_parcelle,
    lot1_numero,
    type_local,
    TRY_CAST(surface_reelle_bati AS DOUBLE)     AS surface_reelle_bati,
    TRY_CAST(nombre_pieces_principales AS INTEGER) AS nombre_pieces_principales,
    nature_culture,
    TRY_CAST(surface_terrain AS DOUBLE)         AS surface_terrain,
    TRY_CAST(longitude AS DOUBLE)               AS longitude,
    TRY_CAST(latitude AS DOUBLE)                AS latitude
FROM read_csv(
    '{{raw_glob}}',
    header = true,
    union_by_name = true,
    all_varchar = true
);
