-- Coastal premium: price per m² in coastal vs inland communes, by type
WITH s AS (
    SELECT t.type_local, dc.est_littorale,
           COUNT(*) AS ventes, MEDIAN(f.prix_m2) AS prix_m2_median
    FROM fact_ventes f
    JOIN dim_date d USING (date_key)
    JOIN dim_commune dc USING (code_commune)
    JOIN dim_type_bien t USING (type_bien_key)
    WHERE d.annee = (SELECT annee_ref FROM param)
    GROUP BY ALL
)
SELECT type_local,
       MAX(ventes) FILTER (WHERE est_littorale)             AS ventes_littoral,
       ROUND(MAX(prix_m2_median) FILTER (WHERE est_littorale))     AS prix_m2_littoral,
       MAX(ventes) FILTER (WHERE NOT est_littorale)         AS ventes_arriere_pays,
       ROUND(MAX(prix_m2_median) FILTER (WHERE NOT est_littorale)) AS prix_m2_arriere_pays,
       ROUND(100 * (MAX(prix_m2_median) FILTER (WHERE est_littorale)
                  / MAX(prix_m2_median) FILTER (WHERE NOT est_littorale) - 1), 1) AS prime_littorale_pct
FROM s GROUP BY 1 ORDER BY 1;
