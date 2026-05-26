# Adventure Game

## Présentation

Adventure Game est un jeu 2D réalisé en Python avec la bibliothèque Arcade dans le cadre du projet du cours d’informatique.
Le joueur contrôle un aventurier qui doit explorer différentes cartes, éviter des pièges et des monstres, récupérer des cristaux et résoudre de petits mécanismes pour progresser.

Au cours du projet, nous avons progressivement ajouté plusieurs fonctionnalités :

déplacement du joueur et collisions ;
chargement de cartes depuis des fichiers ;
monstres avec comportements différents ;
armes (boomerang et épée) ;
trous et pièges ;
blobs utilisant un système de pathfinding avec navigation mesh ;
extensions personnalisées : coffres avec clés et spikes animés.

Le jeu utilise également des animations, des effets sonores et différentes structures de données pour gérer efficacement les cartes et les entités du jeu.


# Installation

Le projet utilise `uv` pour gérer les dépendances Python.

## Installer les dépendances

Dans un terminal, placez-vous dans le dossier du projet puis exécutez :

`bash`
`uv sync`

# Lancer le jeu

Pour lancer la carte principale :

`bash`
`uv run main.py`

Il est aussi possible de lancer une autre carte :

`bash`
`uv run main.py maps/map1.txt`


# Contrôles

## Déplacements

Flèche haut : déplacer le joueur vers le haut
Flèche bas : déplacer le joueur vers le bas
Flèche gauche : déplacer le joueur vers la gauche
Flèche droite : déplacer le joueur vers la droite

## Actions

 `D` : utiliser l’arme active
 `R` : changer d’arme


# Armes

## Boomerang

Le boomerang est l’arme par défaut.
Il est lancé dans la direction regardée par le joueur puis revient automatiquement après avoir touché un obstacle ou un ennemi.

## Épée

L’épée effectue une attaque courte mais puissante dans la direction actuelle du joueur.
Elle peut également casser des cristaux.


# Monstres

Le jeu contient plusieurs types d’ennemis :

## Spinners

Les spinners se déplacent horizontalement ou verticalement jusqu’à rencontrer un obstacle.

## Chauves-souris

Les chauves-souris volent aléatoirement dans une zone donnée et traversent les obstacles.

## Blobs

Les blobs utilisent un système de navigation intelligent :

* ils patrouillent aléatoirement ;
* ils détectent le joueur grâce à une ligne de vue ;
* ils calculent un chemin avec un navmesh et un algorithme de pathfinding


# Extensions personnalisées

## Coffres et clés

Le joueur peut récupérer des clés permettant d’ouvrir des coffres spéciaux.

## Spikes animés

Les spikes alternent entre un état dangereux et un état inactif.
Le joueur doit observer leur timing pour traverser certaines zones sans mourir.


# Exemple de gameplay

Un exemple typique de partie :

1. Explorer la carte et récupérer des cristaux.
2. Éviter les trous et les monstres.
3. Trouver une clé cachée.
4. Ouvrir un coffre.
5. Traverser une zone de spikes animés.
6. Utiliser le boomerang ou l’épée pour éliminer les ennemis.


# Tests

Le projet contient des tests `pytest` couvrant les principales fonctionnalités :

lecture des maps ;
collisions ;
armes ;
monstres ;
extensions.

Pour exécuter les tests :

`bash`
`uv run pytest`


# Vérifications de qualité

Le projet utilise :

* Ruff pour le style et les annotations ;
* Ty pour les vérifications de types.

Commandes utiles :

`uv run ruff check`
`uv run ty check`

# Crédits

Le jeu a été développé avec :

Python
Arcade
NetworkX

Les assets graphiques principaux proviennent du pack :
Top Down Adventure Pack par o-lobster.
