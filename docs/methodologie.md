# Méthodologie

## Source

**Demandes de valeurs foncières (DVF)**, publiées par la DGFiP : toutes les ventes immobilières enregistrées par les notaires en France (hors Alsace-Moselle et Mayotte). Version utilisée : **Geo-DVF** d'Etalab, qui ajoute la géolocalisation des parcelles. Licence Ouverte 2.0.

## Le grain des données

Une ligne DVF n'est **pas** une vente. C'est un croisement `mutation × parcelle × local × nature de culture`. Une maison avec jardin peut occuper trois lignes, avec la surface habitable répétée trois fois et le prix de vente répété trois fois. Sommer naïvement donne une maison de 360 m² vendue trois fois son prix.

Le pipeline reconstruit donc le grain **une ligne = une vente** (`int_mutations`) :

| Champ | Règle d'agrégation | Pourquoi |
|---|---|---|
| `valeur_fonciere` | `MAX` | répété sur chaque ligne, ne jamais sommer |
| logements | `DISTINCT` sur (parcelle, lot, type, surface, pièces) puis `COUNT` | une maison sur 3 cultures reste 1 logement |
| `surface_terrain` | somme sur (parcelle, culture) distincts | le terrain est bien réparti par culture |
| dépendances | indicateur `avec_dependance` | une cave ne change pas le logement |

## Règles de nettoyage

Chaque vente rejetée reçoit **un motif explicite**, le premier qui s'applique dans cet ordre. Le tableau `audit_nettoyage` donne le décompte, et un contrôle bloquant vérifie que `brut = conservé + rejeté` (aucune ligne ne disparaît en silence).

| # | Motif | Règle | Justification |
|---|---|---|---|
| 01 | Pas une vente simple | `nature_mutation <> 'Vente'` | VEFA, échanges, adjudications : prix non comparables |
| 02 | Aucun logement | pas de maison ni d'appartement | parkings, caves, terrains nus |
| 03 | Vente multi-logements | plus d'un logement | prix global d'un lot : prix au m² sans signification |
| 04 | Vente mixte avec local pro | logement + commerce | une part du prix paie le local |
| 05 | Vente multi-communes | parcelles sur plusieurs communes | impossible à rattacher |
| 06 | Prix ou surface manquant | valeur ou surface nulle | non calculable |
| 07 | Surface hors bornes | < 9 m² ou > 1 000 m² | 9 m² = seuil légal de décence |
| 08 | Prix hors bornes | < 15 000 € ou > 50 M€ | ventes symboliques, erreurs de saisie |
| 09 | Prix au m² aberrant | < 500 ou > 40 000 €/m² | bornes métier pour le 06 |
| 10 | Hors P1-P99 | 1 % de chaque queue, par type et par année | queues résiduelles, s'adapte au marché |

Les seuils sont dans `src/dvf/config.py`, pas dans le SQL : on les modifie en un seul endroit.

## Choix statistiques

- **Médiane, pas moyenne.** Une villa à 15 M€ à Saint-Jean-Cap-Ferrat déplace une moyenne communale ; la médiane est aussi l'indicateur de référence des Notaires de France.
- **Seuil de 30 ventes** avant de publier une médiane par commune. En dessous, c'est du bruit.
- **Année de référence = dernière année complète.** Geo-DVF publie l'année en cours partiellement (environ un semestre de retard). La comparer à une année pleine montrerait une fausse chute de 50 % des volumes.
- **Indices base 100** pour comparer prix et volumes sur un même graphique, plutôt qu'un graphique à double axe qui suggère des croisements arbitraires.

## Limites

- Le prix DVF inclut parfois le mobilier et exclut les frais de notaire ; il n'intègre pas l'état du bien.
- `est_littorale` repose sur un référentiel de 16 communes du 06 (`seeds/communes_littorales_06.csv`), à étendre si le Var est ajouté. Un contrôle qualité signale tout code absent des données.
- Pas d'information sur l'étage, la vue, l'état ou le DPE : la « prime littorale » mesure la commune, pas la vue mer.
- Délai de publication : environ 6 mois entre la signature et la mise à disposition.

## Modèle de prix (régression hédonique)

**Question :** une commune est-elle chère, ou y vend-on surtout des biens chers au m² (studios) ?

**Spécification :** moindres carrés ordinaires sur le logarithme du prix au m².

```
log(prix_m2) = commune + type de bien + typologie + année + dépendance + ε
```

- Variables catégorielles en effets fixes. Références : la commune la plus active (Nice en pratique), appartement, T3, première année.
- `exp(coefficient) - 1` = écart de prix au m² en %, **toutes choses égales par ailleurs**.
- Erreurs standard robustes à l'hétéroscédasticité (HC1).
- Communes de moins de 30 ventes regroupées dans « Autres communes ».
- Ventes de l'année en cours exclues (année incomplète).
- La surface de terrain est volontairement exclue : presque toutes les maisons en ont, et en DVF les appartements portent la parcelle de la copropriété. La variable dupliquerait « maison » (colinéarité parfaite) ; le pipeline refuse d'ailleurs tout modèle de rang incomplet.

**Indice brut vs ajusté :** pour chaque commune, l'indice brut compare les médianes (référence = 100), l'indice ajusté compare les coefficients du modèle. L'écart entre les deux mesure **l'effet de composition** : la part du prix apparent due au type de biens vendus.

**Validation :** le générateur de données synthétiques (`src/dvf/demo.py`) plante des effets connus (T1 +18 %, 2022 +11 %…). Un test vérifie que le modèle les retrouve à ±2,5 points.

**Limites :** R² modéré, attendu : DVF ne contient ni l'étage, ni la vue, ni l'état, ni le DPE, qui expliquent une grande partie du prix. Le modèle mesure des effets moyens, pas un prix d'estimation individuel.
