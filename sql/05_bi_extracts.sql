-- =====================================================================
-- 05_bi_extracts.sql : flat extract for Tableau.
-- Power BI consumes the star schema directly; Tableau Public works best
-- with one wide, denormalised table (it only reads text/Excel files).
-- =====================================================================

CREATE OR REPLACE TABLE tableau_ventes AS
SELECT
    f.id_mutation                         AS "Id Vente",
    d.date                                AS "Date",
    d.annee                               AS "Année",
    d.trimestre_libelle                   AS "Trimestre",
    d.mois_libelle                        AS "Mois",
    d.mois                                AS "Mois Num",
    d.saison                              AS "Saison",
    c.code_commune                        AS "Code Commune",
    c.nom_commune                         AS "Commune",
    c.nom_departement                     AS "Département",
    CASE WHEN c.est_littorale THEN 'Littoral' ELSE 'Arrière-pays' END AS "Zone",
    t.type_local                          AS "Type de bien",
    f.typologie                           AS "Typologie",
    f.nb_pieces                           AS "Pièces",
    f.surface_bati                        AS "Surface (m²)",
    CASE WHEN f.surface_bati < 30 THEN '1. < 30 m²'
         WHEN f.surface_bati < 50 THEN '2. 30-50 m²'
         WHEN f.surface_bati < 80 THEN '3. 50-80 m²'
         WHEN f.surface_bati < 120 THEN '4. 80-120 m²'
         ELSE '5. 120 m² et +' END        AS "Tranche de surface",
    f.surface_terrain                     AS "Terrain (m²)",
    CASE WHEN f.avec_dependance THEN 'Oui' ELSE 'Non' END AS "Avec dépendance",
    f.valeur_fonciere                     AS "Prix",
    f.prix_m2                             AS "Prix m²",
    f.latitude                            AS "Latitude",
    f.longitude                           AS "Longitude",
    c.latitude                            AS "Latitude Commune",
    c.longitude                           AS "Longitude Commune"
FROM fact_ventes f
JOIN dim_date d USING (date_key)
JOIN dim_commune c USING (code_commune)
JOIN dim_type_bien t USING (type_bien_key);
