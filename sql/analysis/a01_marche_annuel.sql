-- Market by year: volumes, median prices, year-over-year change
WITH a AS (
    SELECT d.annee,
           COUNT(*)                     AS ventes,
           MEDIAN(f.prix_m2)            AS prix_m2_median,
           MEDIAN(f.valeur_fonciere)    AS prix_median,
           SUM(f.valeur_fonciere) / 1e6 AS volume_financier_meur,
           COUNT(DISTINCT d.mois)       AS n_mois
    FROM fact_ventes f JOIN dim_date d USING (date_key)
    GROUP BY 1
)
SELECT annee, ventes,
       ROUND(prix_m2_median) AS prix_m2_median,
       ROUND(prix_median)    AS prix_median,
       ROUND(volume_financier_meur, 1) AS volume_financier_meur,
       n_mois = 12           AS annee_complete,
       ROUND(100 * (ventes / LAG(ventes) OVER w - 1), 1)                 AS ventes_evol_pct,
       ROUND(100 * (prix_m2_median / LAG(prix_m2_median) OVER w - 1), 1) AS prix_m2_evol_pct
FROM a
WINDOW w AS (ORDER BY annee)
ORDER BY annee;
