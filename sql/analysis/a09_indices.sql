-- Volume vs price, both indexed to 100 on the first complete year.
-- Shows whether the market adjusts through prices or through volumes.
WITH a AS (
    SELECT d.annee, COUNT(*) AS ventes, MEDIAN(f.prix_m2) AS prix_m2_median
    FROM fact_ventes f JOIN dim_date d USING (date_key)
    WHERE d.annee BETWEEN (SELECT annee_debut FROM param) AND (SELECT annee_ref FROM param)
    GROUP BY 1
)
SELECT annee,
       ROUND(100.0 * ventes / FIRST(ventes ORDER BY annee) OVER (), 1)                 AS indice_volume,
       ROUND(100.0 * prix_m2_median / FIRST(prix_m2_median ORDER BY annee) OVER (), 1) AS indice_prix
FROM a ORDER BY annee;
