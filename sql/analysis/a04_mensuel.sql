-- Monthly series with a 12-month rolling volume (removes seasonality)
WITH m AS (
    SELECT d.annee_mois, MIN(d.date) AS mois_debut,
           COUNT(*) AS ventes,
           MEDIAN(f.prix_m2) AS prix_m2_median
    FROM fact_ventes f JOIN dim_date d USING (date_key)
    GROUP BY 1
)
SELECT annee_mois, mois_debut, ventes,
       ROUND(prix_m2_median) AS prix_m2_median,
       CASE WHEN COUNT(*) OVER w12 = 12 THEN SUM(ventes) OVER w12 END AS ventes_12m_glissants
FROM m
WINDOW w12 AS (ORDER BY mois_debut ROWS BETWEEN 11 PRECEDING AND CURRENT ROW)
ORDER BY mois_debut;
