-- What does {{budget}} € buy? Apartment surface by commune (reference year)
SELECT dc.nom_commune, dc.est_littorale,
       COUNT(*) AS ventes,
       ROUND(MEDIAN(f.prix_m2)) AS prix_m2_median,
       ROUND({{budget}} / MEDIAN(f.prix_m2)) AS surface_pour_budget_m2
FROM fact_ventes f
JOIN dim_date d USING (date_key)
JOIN dim_commune dc USING (code_commune)
JOIN dim_type_bien t USING (type_bien_key)
WHERE t.type_local = 'Appartement' AND d.annee = (SELECT annee_ref FROM param)
GROUP BY ALL
HAVING COUNT(*) >= {{min_ventes}}
ORDER BY surface_pour_budget_m2 DESC;
