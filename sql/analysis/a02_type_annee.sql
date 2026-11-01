-- Apartments vs houses over time
SELECT d.annee, t.type_local,
       COUNT(*)                 AS ventes,
       ROUND(MEDIAN(f.prix_m2)) AS prix_m2_median,
       ROUND(MEDIAN(f.surface_bati)) AS surface_mediane
FROM fact_ventes f
JOIN dim_date d USING (date_key)
JOIN dim_type_bien t USING (type_bien_key)
GROUP BY ALL
ORDER BY 1, 2;
