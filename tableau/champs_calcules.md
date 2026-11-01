# Champs calculés, paramètres et ensembles Tableau

À créer dans le classeur connecté à `tableau_ventes.csv`. Les noms entre crochets correspondent aux colonnes de l'extrait.

## Paramètres

| Nom | Type | Valeurs | Défaut | Usage |
|---|---|---|---|---|
| `p_Budget` | Entier | 100 000 à 1 000 000, pas 25 000 | 300 000 | simulateur |
| `p_Mesure` | Chaîne | Prix m² médian · Nombre de ventes · Prix médian | Prix m² médian | changer la mesure d'une vue |
| `p_Commune` | Chaîne | liste depuis [Commune] | Antibes | comparaison à une commune choisie |
| `p_Seuil bonne affaire` | Flottant | -0,30 à 0, pas 0,05 | -0,15 | seuil « sous le marché » |

## Mesures de base

```
// Ventes
COUNTD([Id Vente])

// Prix m² médian
MEDIAN([Prix m²])

// Prix m² médian (fiable) : pas de médiane sur moins de 30 ventes
IF COUNTD([Id Vente]) >= 30 THEN MEDIAN([Prix m²]) END

// Surface accessible (m²)
[p_Budget] / MEDIAN([Prix m²])
```

## Expressions LOD (le point fort de Tableau)

```
// Médiane de la commune, même année et même type
{ FIXED [Commune], [Année], [Type de bien] : MEDIAN([Prix m²]) }

// Écart à la médiane communale (par vente)
[Prix m²] / { FIXED [Commune], [Année], [Type de bien] : MEDIAN([Prix m²]) } - 1

// Statut de la vente
IF [Écart à la médiane communale] <= [p_Seuil bonne affaire] THEN "Sous le marché"
ELSEIF [Écart à la médiane communale] >= -[p_Seuil bonne affaire] THEN "Au-dessus du marché"
ELSE "Dans le marché" END

// Médiane du département sur l'année (référence, ignore le filtre Commune)
{ FIXED [Année], [Type de bien] : MEDIAN([Prix m²]) }

// Indice commune vs département (100 = département)
100 * MEDIAN([Prix m²]) / MIN({ FIXED [Année], [Type de bien] : MEDIAN([Prix m²]) })

// Part des ventes de la commune dans le département
COUNTD([Id Vente]) / MIN({ FIXED [Année] : COUNTD([Id Vente]) })
```

Note : pour que l'indice département ignore le filtre Commune, garder ce filtre en filtre de **dimension** (il s'applique après les FIXED). Mettre Année et Type de bien en filtres **de contexte** pour qu'ils s'appliquent avant.

## Calculs de table

```
// Évolution N-1 (calcul le long de [Année])
(MEDIAN([Prix m²]) - LOOKUP(MEDIAN([Prix m²]), -1)) / ABS(LOOKUP(MEDIAN([Prix m²]), -1))

// Ventes 12 mois glissants (le long de MOIS([Date]) continu)
WINDOW_SUM(COUNTD([Id Vente]), -11, 0)

// Rang des communes (calcul le long de [Commune])
RANK_DENSE([Prix m² médian (fiable)], 'desc')

// Indice base 100 sur la première année
MEDIAN([Prix m²]) / LOOKUP(MEDIAN([Prix m²]), FIRST()) * 100
```

## Mesure dynamique

```
// Mesure choisie
CASE [p_Mesure]
WHEN "Prix m² médian" THEN MEDIAN([Prix m²])
WHEN "Nombre de ventes" THEN COUNTD([Id Vente])
WHEN "Prix médian" THEN MEDIAN([Prix])
END

// Titre dynamique (dans le titre de la feuille : <Titre mesure>)
[p_Mesure] + " par commune"
```

## Comparaison à une commune choisie

```
// Est la commune choisie
[Commune] = [p_Commune]

// Écart à la commune choisie
MEDIAN([Prix m²]) / MIN({ FIXED [Année], [Type de bien] :
    MEDIAN(IF [Commune] = [p_Commune] THEN [Prix m²] END) }) - 1
```

## Ensemble et action d'ensemble

1. Clic droit sur [Commune] > Créer > **Ensemble** : `s_Communes comparées` (vide au départ).
2. Tableau de bord > Actions > **Modifier les valeurs de l'ensemble** : la sélection sur la carte ajoute les communes à l'ensemble.
3. Dans la courbe d'évolution, mettre l'ensemble sur Couleur : IN = bleu, OUT = gris clair. L'utilisateur clique sur des communes de la carte et les voit ressortir sur la courbe.

## Couleurs

Reprendre la palette du projet (cohérente avec Power BI) : bleu `#2a78d6`, orange `#eb6834`, gris `#a3a29c`. Palette divergente pour l'écart au marché : orange (sous) → gris clair (0) → bleu (au-dessus), centrée sur 0.
