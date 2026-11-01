# Construire le tableau de bord Power BI

Temps estimé : 3 à 4 heures. Prérequis : `make all` exécuté, Power BI Desktop installé.

## 1. Importer le modèle

1. Power BI Desktop > **Obtenir des données > Dossier**, ou **Parquet** fichier par fichier.
2. Importer depuis `outputs/powerbi/` : `fact_ventes`, `dim_date`, `dim_commune`, `dim_type_bien`, `audit_nettoyage`.
3. Dans Power Query, vérifier les types : `code_commune` en **Texte** (sinon « 06088 » devient 6088), `date` en **Date**, `prix_m2` et `valeur_fonciere` en **Nombre décimal**.

## 2. Relations (vue Modèle)

| De (plusieurs) | Vers (un) | Cardinalité | Filtre |
|---|---|---|---|
| `fact_ventes[date_key]` | `dim_date[date_key]` | *:1 | Unique |
| `fact_ventes[code_commune]` | `dim_commune[code_commune]` | *:1 | Unique |
| `fact_ventes[type_bien_key]` | `dim_type_bien[type_bien_key]` | *:1 | Unique |

`audit_nettoyage` reste sans relation (table d'information).

Puis :
- Clic droit sur `dim_date` > **Marquer comme table de dates** > colonne `date`.
- `dim_date[mois_libelle]` : **Trier par colonne** `mois`. Même chose pour `trimestre_libelle` avec `date_key`.
- Masquer les clés techniques (`date_key`, `type_bien_key`) dans la vue rapport.
- `dim_commune[latitude]` et `[longitude]` : catégorie de données **Latitude** / **Longitude**.

## 3. Mesures

1. Créer une table vide `_Mesures` (Accueil > Entrer des données).
2. Créer le paramètre What-if **Budget** (100 000 à 1 000 000, pas 25 000, défaut 300 000).
3. Copier les mesures de `mesures.dax` une par une, en les rangeant dans des dossiers d'affichage : *Volumes*, *Prix*, *Comparaisons*, *Simulateur*, *Textes*.
4. Formats : `%` pour les évolutions, `# ##0 €` pour les prix.

## 4. Thème

Affichage > Thèmes > **Parcourir les thèmes** > `theme_cote_azur.json`.

## 5. Les pages

Format de page 16:9. Bandeau de filtres en haut de chaque page : **Année**, **Type de bien**, **Commune** (synchronisés entre les pages via Affichage > Synchroniser les segments).

### Page 1 : Vue d'ensemble
- 4 cartes KPI : `Ventes`, `Prix m² médian`, `Prix médian`, `Volume financier (M€)`. Sous chacune, une petite carte avec l'évolution N-1 et la mesure `Couleur évolution` en mise en forme conditionnelle.
- Graphique en courbes : `Ventes 12 mois glissants` par `annee_mois`.
- Graphique en courbes séparé : `Prix m² médian 12 mois glissants` par `annee_mois`. **Deux graphiques, pas un double axe.**
- Zone de texte avec la mesure `Titre prix` en titre de page.

### Page 2 : Carte et communes
- Visuel **Carte** (ou Azure Maps) : latitude/longitude de `dim_commune`, taille = `Ventes`, couleur = `Prix m² médian (fiable)` en dégradé bleu.
- Tableau classé : commune, `Rang commune (prix)`, `Prix m² médian (fiable)`, `Prix m² évol. %` (icônes), `Ventes`, `Écart vs département %` (barres de données).
- Graphique à barres : `Prime littorale %` par type de bien.

### Page 3 : Tendances
- Petits multiples : `Prix m² médian` par `annee`, petits multiples = `nom_commune`, filtré sur les communes clés (Antibes, Nice, Cannes, Menton, Cagnes-sur-Mer, Grasse).
- Histogramme : part des ventes par `mois_libelle` (saisonnalité).
- Barres : `Prix m² médian` par `typologie` (Appartement uniquement).

### Page 4 : Simulateur de budget
- Segment du paramètre **Budget** (curseur).
- Carte : mesure `Titre budget`.
- Barres horizontales : `Surface accessible (m²)` par commune, triées.
- C'est la page la plus parlante en entretien : la démontrer en direct.

### Page 5 : Qualité des données
- Barres : `audit_nettoyage[nb_mutations]` par `etape` (l'entonnoir de nettoyage).
- Texte : les règles de nettoyage (reprendre `docs/methodologie.md`).
- Mesure `Période des données` en pied de page sur toutes les pages.

## 6. Finitions

- **Info-bulles** personnalisées sur la carte : page info-bulle avec prix, évolution, ventes, surface médiane.
- **Signets** : bouton « Appartements / Maisons » sur la page 1.
- **Navigation** : boutons de page en haut à gauche.
- Texte alternatif sur chaque visuel (accessibilité).

## 7. Publier

1. Enregistrer `dvf_cote_azur.pbix` dans `powerbi/`.
2. Publier sur le service Power BI > **Publier sur le web** (données publiques, aucun risque) pour obtenir un lien public.
3. Ajouter le lien dans le README, sur LinkedIn et sur le portfolio.
4. Exporter chaque page en PNG dans `images/` (pbi_page1.png, etc.) et enregistrer un GIF de 20 secondes de navigation (ScreenToGif, gratuit) : `images/demo_dashboard.gif`.

> Si « Publier sur le web » est bloqué par le compte, exporter le rapport en PDF et le mettre dans `powerbi/`. Les captures et le GIF dans le README suffisent la plupart du temps : les recruteurs n'ouvrent pas le .pbix.
