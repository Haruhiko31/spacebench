# Bienvenue sur SpaceBench

**SpaceBench** est une plateforme de benchmark open-source pour la **Détermination Précise d'Orbite (LEO-POD)**, publiée sous la [licence MIT](https://opensource.org/licenses/MIT) et développée dans le cadre d'un mémoire de Master à l'Université de Namur.

Elle permet aux chercheurs et ingénieurs de téléverser des fichiers géodésiques, de configurer un modèle orbital et un estimateur, de lancer un pipeline POD complet, et de comparer la précision des résultats via un tableau de bord interactif.

---

## Qu'est-ce que la Détermination Précise d'Orbite ?

La Détermination Précise d'Orbite (POD) est le processus de calcul de la trajectoire d'un satellite en orbite basse (LEO) avec une précision centimétrique, en utilisant les observations GPS embarquées combinées aux produits précis d'orbites et d'horloges de satellites fournis par l'International GNSS Service (IGS).

SpaceBench se concentre sur l'approche **non-différenciée (zéro-différence)** : une technique monorecepteur où l'horloge du récepteur LEO est estimée époque par époque, et les horloges des satellites GPS sont corrigées à l'aide des enregistrements IGS CLK_30S.

---

## Ce que fait SpaceBench

| Étape             | Description |
|-------------------|-------------|
| **Upload**        | Accepte 4 fichiers d'entrée : observations RINEX embarquées, orbite de référence RSO, orbites précises IGS, et corrections d'horloges IGS |
| **Configuration** | Choisir le modèle orbital cinématique et un estimateur pour le MVP : moindres carrés ou plugin Python personnalisé |
| **Exécution**     | Lance le pipeline POD comme tâche de fond asynchrone avec des logs par phase |
| **Comparaison**   | Affiche les résultats RMS (3D, Radial, Along-track, Cross-track) dans un tableau triable et un histogramme |

---

## Compatibilité de mission

SpaceBench est agnostique en termes de mission. Tout satellite LEO fournissant des observations RINEX 2 embarquées et une orbite de référence RSO SP3 peut être utilisé, associé à des produits IGS SP3 et CLK_30S de toute source compatible.

Le tableau de bord est pré-rempli avec des données de démonstration. Des fichiers d'entrée réels sont fournis pour la mission **CHAMP** :

| Jour | Date |
|------|------|
| D200 | 2010-07-19 |
| D201-D219 | 2010-07-20 à 2010-08-07 |
| D246 | 2010-09-03 |
