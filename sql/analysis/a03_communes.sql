-- Commune ranking on the reference year, with change vs previous year.
-- Communes with fewer than {{min_ventes}} sales are excluded: a median on
-- 8 sales is noise, not a price.
WITH c AS (
    SELECT f.code_commune, d.annee,
           COUNT(*) AS ventes,
           MEDIAN(f.prix_m2) AS prix_m2_median
    FROM fact_ventes f JOIN dim_date d USING (date_key)
    WHERE d.annee IN ((SELECT annee_ref FROM param), (SELECT annee_ref - 1 FROM param))
    GROUP BY ALL
),
par_commune AS (
    SELECT code_commune,
           MAX(ventes)         FILTER (WHERE annee = (SELECT annee_ref FROM param))     AS ventes,
           MAX(prix_m2_median) FILTER (WHERE annee = (SELECT annee_ref FROM param))     AS prix_m2_median,
           MAX(prix_m2_median) FILTER (WHERE annee = (SELECT annee_ref - 1 FROM param)) AS prix_m2_median_n1,
           MAX(ventes)         FILTER (WHERE annee = (SELECT annee_ref - 1 FROM param)) AS ventes_n1
    FROM c GROUP BY 1
)
SELECT DENSE_RANK() OVER (ORDER BY p.prix_m2_median DESC) AS rang,
       dc.nom_commune, dc.est_littorale, p.ventes,
       ROUND(p.prix_m2_median) AS prix_m2_median,
       ROUND(100 * (p.prix_m2_median / p.prix_m2_median_n1 - 1), 1) AS prix_m2_evol_pct,
       ROUND(100 * (p.ventes / p.ventes_n1 - 1), 1) AS ventes_evol_pct
FROM par_commune p JOIN dim_commune dc USING (code_commune)
WHERE p.ventes >= {{min_ventes}}
ORDER BY rang;
