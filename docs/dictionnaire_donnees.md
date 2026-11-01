# Dictionnaire de données

## fact_ventes
Une ligne par vente de logement nettoyée.

| Colonne | Type | Description |
|---|---|---|
| `id_mutation` | texte | Identifiant unique de la vente (clé primaire) |
| `date_key` | entier | Date de signature, format AAAAMMJJ → `dim_date` |
| `code_commune` | texte | Code INSEE (5 caractères) → `dim_commune` |
| `type_bien_key` | entier | → `dim_type_bien` |
| `valeur_fonciere` | décimal | Prix de vente en € (hors frais de notaire) |
| `surface_bati` | décimal | Surface réelle bâtie en m² |
| `nb_pieces` | entier | Nombre de pièces principales |
| `typologie` | texte | T1, T2, T3, T4, T5+ ou Non renseigné |
| `surface_terrain` | décimal | Surface de terrain en m² (0 si aucune) |
| `avec_dependance` | booléen | Vente avec cave, parking ou garage |
| `prix_m2` | décimal | `valeur_fonciere / surface_bati` |
| `latitude`, `longitude` | décimal | Centroïde des parcelles de la vente |

## dim_date
Calendrier continu (une ligne par jour, années pleines).

| Colonne | Description |
|---|---|
| `date_key` | AAAAMMJJ (clé) |
| `date` | Date |
| `annee`, `trimestre`, `mois` | Composantes |
| `trimestre_libelle` | ex. « T2 2024 » |
| `annee_mois` | ex. « 2024-06 » |
| `mois_libelle` | ex. « juin » |
| `saison` | Hiver, Printemps, Été, Automne |

## dim_commune

| Colonne | Description |
|---|---|
| `code_commune` | Code INSEE (clé) |
| `nom_commune` | Nom le plus récent observé |
| `code_departement`, `nom_departement` | Département |
| `est_littorale` | Commune en bord de mer (référentiel `seeds/`) |
| `latitude`, `longitude` | Médiane des positions des ventes |

## dim_type_bien

| `type_bien_key` | `type_local` |
|---|---|
| 1 | Appartement |
| 2 | Maison |

## audit_nettoyage

| Colonne | Description |
|---|---|
| `etape` | Motif de rejet, ou `99_conservee` |
| `nb_mutations` | Nombre de ventes concernées |
| `pct` | Part du total brut |
