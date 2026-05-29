Structure générale du projet

- La classe GameView est le point central du jeu, elle possède un Player, un Boomerang, une Sword, un WorldSprites et un InteractionSprites. Elle permet au jeu de s'actualiser et de fonctionner à chaque frame (on a séparer les fonctions du gameview en plusieurs fichier pour que le code soit plus lisible (en rassemblant les fonctions qui font une action proche)) :

- world_builder.py crée tous les sprites à partir de Map (WorldSprites, InteractionSprites, SwitchSprite, GateSprite) et calcule les bornes de déplacement des spinners. (fonction à effectué à l'ouverture du jeu, plus jamais rappelées)

- systems.py regroupe les fonctions appelées par GameView à chaque frame : déplacement de la caméra, mise à jour des ennemis, collecte des items

- text.py gère l'affichage de l'ui (score, clés).

WorldSprites regroupe toutes les sprite lists du monde (sols, murs, ennemis, objets collectibles). C'est une dataclass simple qui sert juste à rassembler les sprites. InteractionSprites regroupe les SwitchSprite et GateSprite, les deux éléments du système interrupteur/portail.- La logique des conditions de portail est isolée dans gate_conditions.py(condition_is_true), et les collisions/interactions dans interactions.py. Ces deux modules n'importent pas Arcade, ce qui les rend testables sans fenêtre.


- Tous les ennemies sont regroupés dans un seul fichier ennemies.py. Les ennemis à mouvement complexe Bat et Blob héritent de la classe abstraite Enemy et sont stockés dans WorldSprites.enemies. SpinnerSprite n'hérite pas de Enemy : son déplacement est identique à chaque frame et ne dépend ni du joueur ni du navmesh.

- Les armes ont également été regroupée dans un fichier unique. Boomerang et Sword héritent toutes les deux de Weapon, qui fournit les comportements communs (desactivate, kill_enemies).

- La Map est une dataclass immuable, construite une seule fois au chargement et indépendante d'Arcade. Elle contient la grille, le navmesh, les données des interrupteurs et des portails. Elle est stockée dans un fichier map.py.





PARTIE QUESTION DE DESIGN :


1) a) Question de design : PlayerComment définissez-vous le type Direction, et pourquoi ?

Pour gérer l'orientation du joueur, nous utilisons une énumération (Enum) nommée Direction dans le fichier player.py. Elle contient les quatre directions cardinales : NORTH, SOUTH, EAST et WEST.Ce choix permet de rendre le code beaucoup plus propre et d'éviter les erreurs. À la place de chaînes de caractères (comme "north") ou de nombres (comme 2), l'énumération limite les choix possibles aux quatre directions. Dans le code, écrire Direction.SOUTH est plus lisible et plus sûr que d'utiliser une valeur brute. La classe Player possède un attribut direction (initialisé à Direction.SOUTH) qui sert ensuite à afficher les bonnes animations et à orienter les attaques, comme le lancer du boomerang ou le coup d'épée.

b) Ces méthodes reçoivent-elles n’importe quel symbol: int, comme dans on_key_press, ou reçoivent-elles un type de données plus spécifique ? Pourquoi ce choix ?

Dans notre code, la méthode player_move de la classe Player ne reçoit pas directement l'entier symbol: int d'Arcade. Les tâches sont séparéés : la classe GameView s'occupe de détecter les touches pressées et relâchées dans on_key_press et on_key_release, puis elle change la valeur de plusieurs booléens (up_pressed, down_pressed, etc.) qui sont des attribut du Player.La méthode player_move utilise ensuite uniquement ces variables booléennes pour calculer la vitesse (change_x et change_y) et mettre à jour la direction. Ce choix permet de bien séparer le moteur graphique (Arcade) de la logique du joueur. Le joueur ne dépend pas des événements du clavier, il réagit juste à des indicateurs de mouvement.

2) Comment gérez-vous les trous dans la map et la collision avec le joueur ?

Les trous sont stockés dans map.py avec la valeur GridCell.HOLE. Quand le fichier de la carte est lu, le caractère O est transformé en case HOLE. Lors du lancement du jeu dans GameView, chaque trou devient un sprite qui est ajouté dans la liste self.holes. Ensuite, à chaque frame, la méthode restart_if_collision calcule la distance entre le joueur et chaque trou. Si le joueur s'approche trop près d'un trou, le jeu recrée une nouvelle GameView avec la même carte, ce qui recommence la partie. Les trous sont donc gérés différemment des murs : ils ne bloquent pas le joueur sur place, mais ils provoquent sa mort dès qu'il marche dessus.

3)  Question de design : Boomerang a) Avez-vous défini une classe séparée pour gérer le boomerang, et si oui, étend-elle une classe de sprite ? Pourquoi ?

Oui, le boomerang est géré par une classe spécifique nommée Boomerang dans le fichier weapons.py. Elle hérite de la classe Weapon, qui elle-même hérite de arcade.TextureAnimationSprite.La classe parente Weapon contient deux méthodes utiles pour toutes les armes : desactivate (pour activer ou désactiver l'arme) et kill_enemies (pour gérer les collisions et éliminer les monstres). Grâce à cela, le boomerang possède toutes les propriétés d'un sprite animé d'Arcade (position, image, mouvements, collisions). Toute la logique (vitesse, distance maximale, phase de retour vers le joueur) est regroupée dans cette classe. GameView n'a pas à gérer les détails, elle doit juste afficher le boomerang et appeler la méthode update_boomerang.

b) Comment gérez-vous les 3 états du boomerang ?

Les trois états du boomerang sont gérés avec l'énumération BoomerangState dans weapons.py. Les trois valeurs sont INACTIVE, LAUNCHING et RETURNING. Au début, le boomerang est INACTIVE et reste invisible. Quand le joueur appuie sur la touche D, la méthode launch vérifie que l'arme est bien inactive, puis la fait passer à l'état LAUNCHING. Le boomerang avance alors en ligne droite jusqu'à ce qu'il rencontre un mur ou qu'il atteigne la distance de délacement maximale. À ce moment-là, il passe à l'état RETURNING, change sa trajectoire pour revenir vers la position actuelle du joueur, et repasse à l'état INACTIVE dès qu'il est assez proche de lui.

4) Question de design : Epée a) Comment gérez-vous le fait que vous avez maintenant deux types d’armes, avec des comportements différents ? Pensez-vous que vous pourriez ajouter une troisième arme sans tout refaire?


Les classes Boomerang et Sword héritent de la même classe de base Weapon (dans weapons.py). Comme cette classe hérite des sprites d'Arcade, les deux armes partagent le même fonctionnement pour la position, l'affichage et les collisions avec les ennemis. Ensuite, chaque arme garde son comportement: le Boomerang utilise ses trois états pour faire des allers-retours, tandis que la Sword fait une attaque rapide à courte portée en fonction d'où regarde le joueur. Dans GameView, on utilise une variable active_weapon (qui vaut WeaponType.BOOMERANG ou WeaponType.SWORD) pour savoir quelle arme est sélectionnée. La touche R permet de changer d'arme, et la touche D déclenche l'attaque de l'arme en cours.Pour ajouter une troisième arme, il suffit de créer une nouvelle classe qui hérite de Weapon, et d'écrire ses propres règles de mouvement. Il faudrait aussi l'ajouter dans l'énumération WeaponType et modifier la gestion des touches dans GameView, mais tout le reste du système de jeu n'aurait pas besoin d'être réécrit.

b) Si un monstre attaque le joueur “par derrière” pendant que l’épée est active, que devrait-il se passer ? Est-ce que votre implémentation a le comportement attendu ?

Dans notre implémentation, le joueur et l'épée sont deux sprites bien distincts. L'épée élimine les monstres qu'elle touche en face du joueur, mais elle ne rend pas le joueur invincible. Si un monstre arrive par-derrière et touche le joueur pendant que l'épée est active, la collision est détectée normalement par la méthode restart_if_collision et la partie recommence.Ce comportement est celui attendu : l'épée sert uniquement à attaquer dans une zone précise, elle ne protège pas le reste du corps du joueur contre les attaques par derrière.


5) Question de design : Chauve-Souris a) Comment gérez-vous le fait que vous avez maintenant deux types de monstres, avec des comportements différents ? Pensez-vous que vous pourriez ajouter un troisième monstre sans tout refaire ?

Spinner et Bat sont deux classes indépendantes qui héritent de arcade.TextureAnimationSprite, sans classe mère commune. On n'en a pas créé une car leur fonctionnement est trop différentes : le spinner n'a besoin d'aucun paramètre pour se déplacer. Une classe mère commune aurait forcé le spinner à implémenter une méthode avec des paramètres qu'il n'utilise pas. De plus, avec un seul ennemi "intelligent" (chauve-souris). Pour ajouter un troisième monstre, cela dépend de son type : si c'est un ennemi au comportement intelligent (qui réagit au joueur ou à l'environnement comme la chauve-souris), on créerait une classe mère avec une asbstractméthode move() commune, et on ferait hériter Bat et ce nouvel ennemi de celle-ci. Si c'est un ennemi au mouvement déterministe comme le spinner, on créerait simplement une nouvelle classe héritant de arcade.TextureAnimationSprite avec sa propre logique de déplacement, sans modifier les classes existantes.

6) Questions de design : Blobs a) Qu’avez-vous choisi comme type de nœud TypeNoeud ? Pourquoi ?

Pour représenter les nœuds du navmesh, nous avons choisi un simple tuple de nombres décimaux : tuple[float, float], qui correspond aux coordonnées (x, y) en pixels.Ce choix est très pratique : ce type de données peut être utilisé comme clé (il est hashable), ce qui est obligatoire pour travailler avec la bibliothèque NetworkX. De plus, il fonctionne directement avec les fonctions d'Arcade (comme has_line_of_sight) et de NetworkX (comme dijkstra_path), sans avoir besoin de créer une classe supplémentaire. Les nombres décimaux (float) sont indispensables car si on utilisait des entiers (int), on aurait des problèmes d'arrondis lorsque la division entre la taille des cases et la densité du navmesh ne tombe pas juste. Nous avons arrondi les coordonnées des nœuds à la 6e décimale afin d'éviter les erreurs de précision des flottants. Sans cet arrondi, deux calculs censés produire la même position pouvaient donner des valeurs légèrement différentes, empêchant Dijkstra de retrouver le nœud dans le graphe et provoquant une boucle infinie pour la recherche du chemin.

b) À quel niveau traitez-vous la construction du navmesh, et où le stockez-vous ? Pourquoi ces choix ?

Le navmesh est construit directement dans le fichier map.py par la méthode _build_navmesh (appelée pendant le chargement de la carte), et il est stocké dans l'attribut Map.navmesh. Ce choix permet de regrouper toutes les informations au même endroit : l'objet Map contient la grille du niveau, les positions de départ et le navmesh (qui fait partie de la map sauf qu'il est invisible). La classe GameView n'a pas à s'occuper de la création du graphe, elle a juste à lire self.map.navmesh quand elle en a besoin.

c) Pouvez-vous tester la construction du navmesh sans dépendre de Arcade ?

Oui. Les fonctions build_navmesh et load_map_from_string utilisent uniquement Networkx et le fichier des constantes, il n'y a aucun import de la bibliothèque Arcade à ce niveau-là. On peut donc écrire un test unitaire classique, charger une carte sous forme de str, et vérifier le nombre de nœuds, les liaisons ou le fonctionnement de Dijkstra sans avoir besoin d'ouvrir une fenêtre de jeu.


d) Si vous avez n×n nœuds par cellule et une carte m×m, quelle est la complexité quelle est la complexité de vos différents algorithmes ?


Construction du navmesh : O(m²*n²). On parcourt les m*m (m²) cellules de la map, et chaque cellule marchable peut créer n² nœuds. Pour chaque nœud, le code vérifie seulement un nombre constant de voisins ou de cases proches, donc cela ne change pas l'ordre de grandeur.

Recherche de chemin avec Dijkstra : NetworkX utilise un algorithme dont la complexité est environ O((|V| + |E|) log |V|). Dans notre navmesh, chaque nœud a au plus 8 voisins, donc |E| est proportionnel à |V|. Avec |V| = m²*n², cela donne environ O(m²*n²*log(m²*n²)).

Déplacement du blob : une frame simple est en O(1) si le blob suit déjà un chemin, car il avance seulement vers le prochain point. Par contre, quand il choisit une nouvelle destination ou poursuit le joueur, il peut recalculer un chemin, et cette frame devient plus coûteuse à cause de Dijkstra (mais c'est un cas très rare en rapport du nombre de frame).


7) Question de design : Interrupteurs et portails a) Quelle structure de données utilisez-vous pour représenter les conditions d’ouverture des portails ? Pourquoi ?

Pour représenter les conditions d'ouverture des portails, on a utiliser un dictionnaire récursif avec le type GateCondition dans le fichier gate_conditions.py. Cette structure ressemble beaucoup au format du fichier YAML. Par exemple, une condition simple comme switch_is_on: first(identifiant du switch) devient le dictionnaire {"switch_is_on": "first"}. Pour les conditions plus complexes utilisant des opérateurs comme and, or ou not, le dictionnaire contient une liste de sous-conditions. C'est le meilleur choix car cela correspond bien à la logique des formules, et la fonction condition_is_true peut s'évaluer facilement en s'appelant elle-même sur les sous-dictionnaires.

b) Pouvez-vous tester l’évaluation des formules logiques sans dépendre de Arcade ?

Oui, on peut tester toute la logique des formules sans utiliser Arcade car le code est isolé dans gate_conditions.py. La fonction condition_is_true prend seulement deux paramètres : une condition (GateCondition) et un dictionnaire contenant l'état de chaque interrupteur (True ou False).On peut donc tester le fonctionnement des conditions (and, or, not) avec de simples dictionnaires de test, sans avoir besoin de charger des graphismes, des sprites ou une interface GameView.

c) S’il y a n interrupteurs et m portails, et en supposant que chaque condition de portail n’est qu’un unique switch_is_on, quelle est la complexité de traitement des portails à chaque frame ?

À chaque frame, la méthode update_gate_states est appelée. Son fonctionnement se fait en deux étapes :Elle construit d'abord un dictionnaire contenant l'état de tous les interrupteurs (ce qui prend un temps de O(n)).Elle parcourt ensuite les m portails. Comme chaque portail possède une condition simple, la vérification se fait instantanément en regardant dans le dictionnaire des interrupteurs (ce qui prend un temps de O(1) par portail, donc O(m au total). Si on additionne ces deux étapes, la complexité totale à chaque frame est O(n+m)

8) Analyse des performances

NAVMESH_DENSITY :

On fait varier NAVMESH_DENSITY (noté n). C'est lui qui détermine le nombre de nœuds créés par cellule (n² noeuds par cellule marchable). Plus n est grand, plus le navmesh est dense et le chargement lent. Avec m fixé à 20, on s'attend à une courbe quadratique en n.

Benchmark.py charge une carte 20×20 vide et mesure le temps de load_map_from_string sur 5 répétitions.
Chargement (NAVMESH_DENSITY fixé à n, carte 20x20)
n = 1 | nb noeuds = 324 | temps moyen par frame = 7.358 ms
n = 2 | nb noeuds = 1156 | temps moyen = 26.093 ms
n = 3 | nb noeuds = 2704 | temps moyen = 60.179 ms
n = 4 | nb noeuds = 4624 | temps moyen = 105.615 ms
n = 5 | nb noeuds = 7396 | temps moyen = 171.383 ms
n = 7 | nb noeuds = 14400 | temps moyen = 341.544 ms
n = 10 | nb noeuds = 29172 | temps moyen = 694.035 ms
n = 14 | nb noeuds = 57188 | temps moyen = 1407.506 ms

On voit bien que le temps grimpe vite quand n augmente. Entre n=1 et n=14, le nombre de noeuds est multiplié par ~176 et le temps par ~180. C'est cohérent avec la complexité Θ(n²).

nombre de blobs :

On mesure le coût de on_update en faisant varier le nombre de blobs (k). On utilise des blobs et pas des chauves-souris parce que les blobs appellent Dijkstra quand ils recalculent leur chemin, ce qui est beaucoup plus représentatif de la charge réelle. Le benchmark tourne sur 300 frames mesurées, on ne compte pas les 10 premières frames car tous les blobs calculent leur premier chemin en même temps à la frame 1, ce qui crée un pic qui fausse la moyenne.

on_update (nombre de blobs k)
k = 1 | temps moyen par frame = 29.261 ms
k = 3 | temps moyen = 41.07 ms
k = 10 | temps moyen = 47.799 ms
k = 30 | temps moyen = 56.792 ms
k = 100 | temps moyen = 111.167 ms
k = 300 | temps moyen = 263.447 ms

La croissance est globalement linéaire. L'écart-type reste élevé parce que certaines frames déclenchent Dijkstra et coûtent beaucoup plus cher que les autres, c'est normal.

9) Extensions personnelles Extension 1 : pics intermittents

On a ajouté un système de pièges avec des pics au sol (GridCell.SPIKES, représentés par le caractère ! sur la carte). Ces pics changent d'état régulièrement grâce à un compte à rebours : lorsqu'ils sont sortis (actifs), ils sont totalement opaques et tuent le joueur s'il marche dessus ; lorsqu'ils sont rentrés (inactifs), ils deviennent transparents et le joueur peut passer sans subir de dégâts. Le code de cette extension se trouve dans interactions.py avec les fonctions update_spikes et should_restart_after_spikes_collision.

Extension 2 : cles, coffres et invincibilité temporaire

La deuxième extension ajoute des clés (caractère k) et des coffres (caractère C) sur la carte. Lorsque le joueur ramasse une clé, son compteur de clés augmente. S'il touche un coffre en possédant au moins une clé, le coffre s'ouvre, une clé est retirée de l'inventaire, et le joueur devient invincible pendant quelques secondes.Cette mécanique apporte un nouvel avantage au joueur, quand il est invincible, toucher un monstre ne relance pas la partie, mais fait disparaître le monstre de l'écran. Ce système est géré dans systems.py et dans la classe Player. Le nombre de clés possédées est affiché à l'écran grâce au module text.py.



PARTIE EXPLICATION DU CODE :

Semaine 1 : Découverte d’Arcade :

La structure de base (GameView, PhysicsEngineSimple, Camera2D) copiée-colée.

Gestion du clavier par booléens. Changer directement change_x dans on_key_press pause un problème : relâcher droite quand gauche est encore enfoncée arrête le joueur. On stocke donc l'état de chaque touche dans un bool et on recalcule la vitesse à chaque frame.

Création des fichiers constants.py et textures.py. Les constantes et les textures sont isolées dans des fichiers pour éviter de répéter les valeurs dans tout le code, améliore la visibilité et garanti que chaque image n'est chargée qu'une seule fois dans le jeu.


Semaine 2  : Maps et monstres

on considère Map comme dataclass immuable, indépendante d'Arcade. Cela permet de tester le chargement, la validation du format et les calculs des limites des spinners sans ouvrir de fenêtre. L'immuabilité (frozen=True) garantit qu'une map chargée ne peut pas être modifiée accidentellement pendant le jeu.

GridCell en Enum. Les types de cellules (GRASS, BUSH, CRYSTAL, SPINNER...) sont un ensemble fini de valeurs connues à l'avance. Un Enum est mieux qu'un str ou un int : une valeur invalide est impossible, et le code est lisible (GridCell.BUSH plutôt que "x" ou 2).

Les limites des spinners sont calculées une seule fois au début à partir de la map à la création du monde. Puisque seuls la position initiale et les buissons (fixes) déterminent jusqu'où un spinner peut aller. On évite de recalculer à chaque frame. Le déplacement des spinner est mis dans uun fichier à part (une class et sa méthode de déplacemnt).

Vérification de la validité de la map, sinon on renvoie une exeption.


Semaine 3 : Trous et boomerang

Classe Player qui hérite de arcade.TextureAnimationSprite. Jusqu'ici, la logique du joueur était surtout dans GameView. On a créé une classe Player qui regroupe tout ce qui concerne le joueur (direction, touches, score, invincibilité, animation) au même endroit.

On a fait un Enum pour la direction, pour les mêmes raisons que le l'Enum de Gridcell.

on_key_press (gère les touches préssées) et met à jour des booléens (up_pressed, down_pressed...). player_move() ne reçoit rien et lit ces booléens directement.

Trous gérés par distance, pas par collision. On utilise donc un calcul de distance (mort si distance ≤ 16 pixels du centre du trou) plutôt que check_for_collision.

Pour le boomerang, on fait une Classe Boomerang qui hérite d'une classe Weapon, elle-même héritant de arcade.TextureAnimationSprite. Le boomerang a besoin d'une position, d'une animation et de collisions. La classe Weapon regroupe le code commun à toutes les armes (desactivate et kill_enemies), l'utilisation de ce polymorphisme permet d'éviter la duplication de code quand on devra ajouter une nouvelle arme.

On gère l'état du boomerang avec BoomerangState en Enum avec 3 états (INACTIVE, LAUNCHING, RETURNING). L'état est privé et mis en lecture seule grâce à une property (car on ne peut pas forcer le boomerang dans un état invalide depuis l'extérieur).

on affiche le score affiché avec une deuxième caméra fixe( pas de déplacement de l'ui).

Semaine 4 : Épée et Chauve-souris

Ajout de la classe Sword qui hérite de Weapon, on a donc juste du écrire le comportement propre à l'épée (attaque directionnelle, durée limitée). Le code commun (desactivate, kill_enemies) est déjà dans Weapon. on cré l'Enum WeaponType (BOOMERANG ou SWORD) pour que le gameview connaisse l'arme actuelle, une alternative aurait été un booléen, mais l'Enum est plus extensible si on veut ajouter une troisième arme.

On créé la bat indépendement des spinner mais dans le meme fichier, pas de classe mère pour SpinnerSprite et Bat : leurs interfaces sont trop différentes. Le spinner n'a besoin d'aucun paramètre pour se déplacer, contrairement à un ennemi intelligent qui aurait besoin et du joueur. Les forcer dans une même abstraction ne serait pas utile. Les deux types d'ennemis sont gérés dans des listes séparées dans GameView


Semaine 5 : Blob et interrupteurs :

On crée une classe abstraite Enemy pour regrouper les deux enemies (blob, et bat) (déplacement intelligent, réaction au joueur). On crée donc Enemy avec @abstractmethod move(navmesh, player_pos). Bat et Blob en héritent. par conséquent GameView boucle sur une seule liste d'ennemis et appelle move() sans connaître le type concret. SpinnerSprite reste à part, sa logique de déplacement n'ayant pas besoin du navmesh ni du joueur.

Navmesh stocké dans Map, indépendant d'Arcade. La construction du navmesh se fait dans map.py lors du chargement, et le résultat est stocké dans Map.navmesh. Cela garde toute la logique de la carte au même endroit. Comme map.py n'importe rien d'Arcade, on peut tester la construction du navmesh et la recherche de chemin avec de simples strings Python, sans fenêtre.

On a ajouté SwitchData et GateData des dataclasses immuables dans map.py
Un nouveau fichier gate_conditions.py est créé, avec le type récursif GateCondition et la fonction condition_is_true(). Il est appelé depuis interactions.py à chaque frame pour mettre à jour l'état des portails. Ce module n'importe rien d'Arcade, ce qui le rend testable sans fenêtre de jeu.

Lecture YAML déléguée à pyyaml. On utilise yaml.safe_load() pour le parsing, et on cré nos propres fonctions de validation (as_int, as_str...) pour vérifier les types et lancer InvalidMapFileException en cas d'erreur.

On a mis 2 méthodes statiques dans Blob. closest_node et random_axis car elles effectuent un calcul sans lire ni modifier l'état du blob.Les déclarer en méthode d'instance aurait été moins rigoureux.
