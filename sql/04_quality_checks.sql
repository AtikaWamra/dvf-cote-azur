-- =====================================================================
-- 04_quality_checks.sql : automated data tests on the model.
-- Each check returns the number of violating rows.
-- severity = 'bloquant' fails the pipeline, 'alerte' is reported only.
-- =====================================================================

SELECT 'Clé primaire fact_ventes unique' AS controle, 'bloquant' AS severite,
       COUNT(*) - COUNT(DISTINCT id_mutation) AS violations
FROM fact_ventes

UNION ALL
SELECT 'Aucune clé étrangère nulle', 'bloquant',
       COUNT(*) FILTER (WHERE date_key IS NULL OR code_commune IS NULL OR type_bien_key IS NULL)
FROM fact_ventes

UNION ALL
SELECT 'Toute vente a une date dans dim_date', 'bloquant', COUNT(*)
FROM fact_ventes f LEFT JOIN dim_date d USING (date_key) WHERE d.date_key IS NULL

UNION ALL
SELECT 'Toute vente a une commune dans dim_commune', 'bloquant', COUNT(*)
FROM fact_ventes f LEFT JOIN dim_commune c USING (code_commune) WHERE c.code_commune IS NULL

UNION ALL
SELECT 'Prix au m² dans les bornes métier', 'bloquant',
       COUNT(*) FILTER (WHERE prix_m2 < {{prix_m2_min}} OR prix_m2 > {{prix_m2_max}})
FROM fact_ventes

UNION ALL
SELECT 'Prix au m² recalculable (valeur / surface)', 'bloquant',
       COUNT(*) FILTER (WHERE ABS(prix_m2 - valeur_fonciere / surface_bati) > 0.01)
FROM fact_ventes

UNION ALL
SELECT 'Réconciliation : brut = conservé + rejeté', 'bloquant',
       ABS((SELECT COUNT(DISTINCT id_mutation) FROM stg_dvf)
         - (SELECT SUM(nb_mutations) FROM audit_nettoyage))

UNION ALL
SELECT 'dim_date continue (aucun jour manquant)', 'bloquant',
       (SELECT DATEDIFF('day', MIN(date), MAX(date)) + 1 - COUNT(*) FROM dim_date)

UNION ALL
SELECT 'Communes littorales du référentiel présentes dans les données', 'alerte', COUNT(*)
FROM seed_communes_littorales s LEFT JOIN dim_commune c USING (code_commune)
WHERE c.code_commune IS NULL

UNION ALL
SELECT 'Coordonnées GPS dans la zone attendue', 'alerte',
       COUNT(*) FILTER (WHERE latitude NOT BETWEEN 42.9 AND 44.5 OR longitude NOT BETWEEN 5.6 AND 7.8)
FROM fact_ventes

UNION ALL
SELECT 'Taux de conservation >= 30 %', 'alerte',
       CASE WHEN (SELECT pct FROM audit_nettoyage WHERE etape = '99_conservee') < 30 THEN 1 ELSE 0 END;
