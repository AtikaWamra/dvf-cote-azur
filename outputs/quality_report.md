# Rapport qualité

| controle                                                      | severite   |   violations | statut   |
|:--------------------------------------------------------------|:-----------|-------------:|:---------|
| Clé primaire fact_ventes unique                               | bloquant   |            0 | OK       |
| Aucune clé étrangère nulle                                    | bloquant   |            0 | OK       |
| Toute vente a une date dans dim_date                          | bloquant   |            0 | OK       |
| Toute vente a une commune dans dim_commune                    | bloquant   |            0 | OK       |
| Prix au m² dans les bornes métier                             | bloquant   |            0 | OK       |
| Prix au m² recalculable (valeur / surface)                    | bloquant   |            0 | OK       |
| Réconciliation : brut = conservé + rejeté                     | bloquant   |            0 | OK       |
| dim_date continue (aucun jour manquant)                       | bloquant   |            0 | OK       |
| Communes littorales du référentiel présentes dans les données | alerte     |            0 | OK       |
| Coordonnées GPS dans la zone attendue                         | alerte     |            0 | OK       |
| Taux de conservation >= 30 %                                  | alerte     |            0 | OK       |
