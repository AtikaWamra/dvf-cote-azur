-- Focus communes, apartments, median price per m² by year
SELECT d.annee, dc.nom_commune,
       COUNT(*) AS ventes,
       ROUND(MEDIAN(f.prix_m2)) AS prix_m2_median
FROM fact_ventes f
JOIN dim_date d USING (date_key)
JOIN dim_commune dc USING (code_commune)
JOIN dim_type_bien t USING (type_bien_key)
WHERE t.type_local = 'Appartement'
  AND dc.nom_commune IN ({{communes_focus}})
  AND d.annee <= (SELECT annee_ref FROM param)
GROUP BY ALL
ORDER BY 2, 1;
