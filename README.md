# Adventure

Adventure est un petit jeu d'action-aventure en 2D réalisé avec la bibliothèque Arcade. Le joueur explore une carte vue du dessus, ramasse des cristaux, évite les dangers et utilise ses armes pour se défendre. Le monde est chargé depuis un fichier texte : cela permet de créer facilement de nouvelles cartes avec des murs, des ennemis, des trous, des interrupteurs, des portails et des objets à collecter.

Pour lancer le jeu avec la carte par défaut, ouvrez un terminal dans le dossier du projet et exécutez :

`uv run main.py`

Il est aussi possible de lancer une carte précise en donnant son chemin en argument. Par exemple :

`uv run main.py maps/map1.txt`

Le joueur se déplace avec les flèches du clavier. La touche `D` utilise l'arme active, et la touche `R` permet de changer entre le boomerang et l'épée. Le boomerang peut toucher des ennemis ou des interrupteurs à distance, puis revenir vers le joueur (il peut tuer également en revenant vers le joueur). L'épée attaque autour du joueur et peut aussi ramasser des cristaux. La touche `Escape` redémarre la partie.

Le but principal est de collecter les cristaux tout en survivant. Les buissons bloquent le passage, les trous font tomber le joueur, les spinners se déplacent en ligne droite, les chauves-souris volent de manière aléatoire, et les blobs peuvent poursuivre le joueur s'ils le voient. Certains portails sont fermés au départ et s'ouvrent seulement quand les bonnes conditions d'interrupteurs sont satisfaites.

Le jeu contient aussi deux extensions personnelles. Les pics intermittents, placés avec le caractère `!` dans les fichiers de map, alternent entre un état dangereux et un état inoffensif. Les clés `k` et les coffres `C` ajoutent un petit objectif supplémentaire : ramasser une clé permet d'ouvrir un coffre, ce qui donne une invincibilité temporaire contre les ennemis.

Pour vérifier le projet, vous pouvez lancer les tests avec :

```bash
uv run pytest
```

Les benchmarks de performance se lancent avec :

```bash
uv run benchmark.py
```

Ils génèrent `benchmarks.csv` avec les mesures brutes et `benchmarks.png` avec deux graphes : le temps de chargement selon la densité du navmesh, et le temps de `on_update` selon le nombre d'ennemis.
