# Tableau : une histoire de données publique

## Pourquoi Tableau en plus de Power BI

Les deux outils ne jouent pas le même rôle dans ce projet :

| | Power BI | Tableau |
|---|---|---|
| Public | décideur, usage récurrent | grand public, recruteurs |
| Format | tableau de bord de pilotage (KPI, filtres, simulateur) | **Story** : un récit guidé en 5 étapes |
| Données | schéma en étoile + DAX | extrait plat + LOD |
| Grain affiché | communes, mois | **chaque vente** sur la carte |
| Diffusion | Publier sur le web | **Tableau Public** (profil visible) |

En entretien : « Power BI pour piloter, Tableau pour raconter. Le même modèle de données alimente les deux. »

Temps estimé : 4 à 5 heures. Prérequis : `make all` exécuté, [Tableau Public](https://public.tableau.com/app/discover) installé (gratuit).

## 1. Connexion

1. Tableau Public > Se connecter > **Fichier texte** > `outputs/tableau/tableau_ventes.csv`.
2. Faire glisser aussi `tableau_communes.csv` et créer une **relation** sur `Commune = nom_commune`.
3. Ajouter `tableau_moteurs_prix.csv` et `tableau_audit.csv` comme sources de données **séparées** (pas de relation).
4. Vérifier les types : `Code Commune` en Chaîne, `Date` en Date, `Latitude`/`Longitude` en rôle géographique Latitude/Longitude.
5. Créer un **extrait** (Tableau Public l'impose) et filtrer à la source si le fichier dépasse 15 millions de lignes (non nécessaire pour le 06).

## 2. Champs

Créer les paramètres, champs calculés, LOD et l'ensemble de `champs_calcules.md`. Les ranger dans des dossiers : *Mesures*, *LOD*, *Calculs de table*, *Paramètres*.

## 3. Les feuilles

| Feuille | Construction |
|---|---|
| **Carte des ventes** | Longitude en colonnes, Latitude en lignes, [Id Vente] en Détail, type de marque **Densité**, couleur bleue. Fond de carte clair. C'est la vue « waouh » : chaque vente est un point. |
| **Carte des écarts** | Même carte, marque Cercle, couleur = `Écart à la médiane communale` (palette divergente centrée sur 0), taille petite. Filtre Type de bien. |
| **Nuage surface / prix** | Surface en colonnes, Prix en lignes, couleur = `Statut de la vente`, info-bulle avec commune, typologie, prix au m². Ligne de tendance par Type de bien. |
| **Calendrier** | Année en lignes, Mois (trié par Mois Num) en colonnes, carré, couleur = Ventes. Tableau en surbrillance : la saisonnalité saute aux yeux. |
| **Évolution** | MOIS(Date) continu, `Ventes 12 mois glissants` ; seconde feuille avec `Indice base 100`. Ensemble `s_Communes comparées` en couleur. |
| **Classement** | Barres horizontales `Mesure choisie` par Commune, triées, avec `p_Mesure` affiché. |
| **Moteurs du prix** | Source `tableau_moteurs_prix`. Niveau en lignes, `effet_pct` en colonnes ; marque Gantt de `ic_bas_pct` avec taille `ic_haut_pct - ic_bas_pct` pour l'intervalle, plus un cercle sur `effet_pct` (axe double synchronisé). |
| **Brut vs ajusté** | Source `tableau_communes`. Commune en lignes, `Measure Values` (indice_brut, indice_ajuste) en colonnes, marque Cercle + ligne via **chemin** : graphique haltère. |
| **Simulateur** | Commune en lignes, `Surface accessible (m²)` en barres, paramètre `p_Budget` affiché en curseur. |
| **Entonnoir qualité** | Source `tableau_audit`, barres par étape. |

**Viz in Tooltip** : dans l'info-bulle de la carte, insérer la feuille *Évolution* filtrée sur la commune survolée (Insérer > Feuille). Les recruteurs Tableau regardent ce détail.

## 4. Les tableaux de bord

Taille fixe 1200 × 800 (Tableau Public s'affiche mieux en taille fixe).

1. **Explorer le marché** : Carte des ventes (grande), Classement, Évolution. Action de filtre carte → classement ; action d'ensemble carte → évolution.
2. **Trouver les bonnes affaires** : Carte des écarts + Nuage surface/prix + paramètre `p_Seuil bonne affaire`. Action de surbrillance entre les deux.
3. **Ce qui fait le prix** : Moteurs du prix + Brut vs ajusté, avec un texte de 2 lignes qui explique « toutes choses égales par ailleurs ».

## 5. La Story (le livrable principal)

Tableau > Nouvelle histoire. Un point = une phrase-titre qui porte le message, pas un nom de graphique. Reprendre les chiffres réels de `outputs/FINDINGS.md`.

1. **« X actes notariés, Y ventes de logements exploitables »** → Entonnoir qualité. Pose la rigueur dès le départ.
2. **« Le marché s'est ajusté par les volumes, pas par les prix »** (adapter selon le résultat réel) → Évolution, indices base 100.
3. **« La mer fait le prix »** → Carte des ventes + carte des écarts.
4. **« Un studio coûte plus cher au m², même à commune égale »** → Moteurs du prix.
5. **« Avec 300 000 €, de X à Y m² selon la commune »** → Simulateur ; laisser le lecteur jouer avec le curseur.

## 6. Publier

1. Fichier > Enregistrer sur Tableau Public. Titre : *Marché immobilier de la Côte d'Azur (DVF)*.
2. Sur le profil Tableau Public : ajouter une description, le lien GitHub et des tags (`Immobilier`, `France`, `DVF`, `OpenData`).
3. Activer « Afficher les feuilles en onglets » : non (la Story suffit).
4. Copier le lien dans le README (`[Voir la Story Tableau](...)`), sur LinkedIn et sur le portfolio.
5. Capturer les points de la Story en PNG dans `images/` : `tab_story1.png` à `tab_story5.png`.
6. Ajouter le lien Tableau Public à la section **Liens** de votre profil LinkedIn.
