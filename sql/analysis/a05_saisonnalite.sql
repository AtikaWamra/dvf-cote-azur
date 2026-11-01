-- Average share of the yearly volume signed each month (complete years only)
WITH m AS (
    SELECT d.annee, d.mois, d.mois_libelle, COUNT(*) AS ventes
    FROM fact_ventes f JOIN dim_date d USING (date_key)
    WHERE d.annee BETWEEN (SELECT annee_debut FROM param) AND (SELECT annee_ref FROM param)
    GROUP BY ALL
),
parts AS (
    SELECT *, 100.0 * ventes / SUM(ventes) OVER (PARTITION BY annee) AS part
    FROM m
)
SELECT mois, mois_libelle, ROUND(AVG(part), 2) AS part_annuelle_pct
FROM parts
GROUP BY ALL
ORDER BY mois;
