-- Apartments by size: small units cost more per m²
SELECT f.typologie,
       COUNT(*) AS ventes,
       ROUND(MEDIAN(f.surface_bati))    AS surface_mediane,
       ROUND(MEDIAN(f.valeur_fonciere)) AS prix_median,
       ROUND(MEDIAN(f.prix_m2))         AS prix_m2_median
FROM fact_ventes f
JOIN dim_date d USING (date_key)
JOIN dim_type_bien t USING (type_bien_key)
WHERE t.type_local = 'Appartement'
  AND d.annee = (SELECT annee_ref FROM param)
  AND f.typologie <> 'Non renseigné'
GROUP BY 1 ORDER BY 1;
