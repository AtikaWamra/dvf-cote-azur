-- Reference year = latest year with sales in all 12 months.
-- The current year is partial in Geo-DVF; comparing it to full years
-- would show a fake "drop" in volumes.
CREATE OR REPLACE TABLE param AS
WITH annees AS (
    SELECT d.annee, COUNT(DISTINCT d.mois) AS n_mois
    FROM fact_ventes f JOIN dim_date d USING (date_key)
    GROUP BY 1
)
SELECT
    COALESCE(MAX(annee) FILTER (WHERE n_mois = 12), MAX(annee)) AS annee_ref,
    MIN(annee) FILTER (WHERE n_mois = 12)                       AS annee_debut
FROM annees;
