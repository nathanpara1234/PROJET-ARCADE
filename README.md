# Adventure

Adventure est un petit jeu d'action-aventure en 2D réalisé. Le joueur explore une carte vue du dessus, ramasse des cristaux, évite les enemies et autres sortes de pièges et utilise ses armes pour se défendre. Le monde est chargé depuis un fichier texte : cela permet de créer facilement une infinité de nouvelles cartes avec des murs, des ennemis, des trous, des interrupteurs, des portails et des objets à collecter. Si votre carte n'est pas valide, un message d'erreur expliquant le problème sera renvoyé par le code.

Pour lancer le jeu avec la carte par défaut, il faut ouvrir un terminal dans le dossier du projet et taper :

`uv run main.py`

Il est aussi possible de lancer une carte précise en donnant son chemin en argument. Par exemple :

`uv run main.py maps/map1.txt`

On déplace le joueur avec les flèches du clavier. La touche "D" utilise l'arme active (affiché en haut à gauche), on peut changer d'arme (épée ou boomerang) avec la touche "R". La touche "Escape" redémarre la partie.

Le boomerang peut toucher des ennemis ou des interrupteurs à distance, puis revenir vers le joueur (soit en rebondissant contre un buisson ou au bout d'une certaine distance parcourue, on ne peut pas le rappeler avec "D"). Il peut tuer également en revenant vers le joueur, mais ne ramasse pas de crystaux. L'épée attaque autour du joueur (élimine tout type d'ennemies sauf les pièges) et peut aussi ramasser des cristaux.

Le but principal est de collecter tous les cristaux de la map tout en survivant. Les buissons bloquent le passage, les trous font tomber le joueur. Les spinners se déplacent en ligne droite et à vitesse constante (seulement entre deux murs, leur déplacement est donc facilement prévisible). Les chauves-souris volent à vitesse constante et changent de direction aléatoirement dans le temps et volent au dessus des buissons. Les blobs peuvent poursuivre le joueur s'ils le voient (dans une certaine zone autour de lui), sinon ils sont en patrouille constante dans leur zone, on peut se cacher derrière des buissons pour ne pas se faire repérer. Bon à savoir : on ne peut pas passer entre deux trous collés.

Certains portails sont fermés au départ et s'ouvrent seulement quand les bonnes conditions d'interrupteurs sont satisfaites (certains s'ouvrent selon une combinaison précise d'interrupteurs activés ou désactivés). On peut marcher sur des interrupteurs, ils ne bloquent pas le passage.

Le jeu contient aussi deux extensions personnelles. Les pièges à pics immobiles, qui alternent entre un état dangereux et un état inoffensif. Les clés "k" et les coffres "C" ajoutent un avantage supplémentaire au joueur : ramasser une clé permet d'ouvrir un coffre, ce qui donne une invincibilité temporaire contre les ennemis et les pièges (sauf trous) et permet même de tuer les ennemies en marchant dessus.

Résumé des touches :

Flèches : déplacer le joueur
D : utiliser l'arme active
R : changer d'arme (boomerang / épée)
Escape : redémarrer la partie
