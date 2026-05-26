# 1) Question de design : Player

## Comment définissez-vous le type Direction, et pourquoi ?

`Direction` est défini dans `player.py` avec une énumération `Enum`. Elle contient les quatre directions possibles du joueur : `NORTH`, `SOUTH`, `EAST` et `WEST`.

Ce choix permet d’éviter d’utiliser des chaînes de caractères comme `"north"` ou des nombres directement dans le code. Avec une énumération, les valeurs possibles sont limitées et plus lisibles. Par exemple, dans le code, `Direction.SOUTH` est plus clair que `2` ou `"south"`. La classe `Player` possède ensuite un attribut `direction`, initialisé à `Direction.SOUTH`, qui est utilisé pour choisir les animations du joueur et la direction des attaques comme le boomerang ou l’épée.


## Ces méthodes reçoivent-elles n’importe quel symbol: int, comme dans on_key_press, ou reçoivent-elles un type de données plus spécifique ? Pourquoi ce choix ?

Dans mon implémentation, la méthode `player_move` de la classe `Player` ne reçoit pas directement le `symbol: int` de Arcade. Les touches sont traitées dans `GameView`, dans `on_key_press` et `on_key_release`, puis elles mettent à jour des booléens du joueur comme `up_pressed`, `down_pressed`, `left_pressed` et `right_pressed`.

Ensuite, `player_move` utilise seulement ces booléens pour calculer `change_x`, `change_y` et mettre à jour la direction du joueur. Ce choix sépare mieux les responsabilités : `GameView` s’occupe des événements clavier Arcade, tandis que `Player` s’occupe seulement de son mouvement.

# 2) Question de design : Trou
## Comment gérez-vous les trous dans la map et la collision avec le joueur ?

Les trous sont représentés dans `map.py` par la valeur `GridCell.HOLE`. Lors du chargement de la map, le caractère `O` qui est transformé en case `HOLE`. Dans `GameView`, chaque case trou devient un sprite ajouté dans la liste `self.holes`.

À chaque frame, la méthode `restart_if_collision` vérifie la distance entre le joueur et chaque trou. Si le joueur est assez proche d’un trou, une nouvelle `GameView` est créée avec la même map, ce qui redémarre la partie. Les trous sont donc gérés séparément des murs : ils ne bloquent pas forcément le joueur comme un buisson, mais ils déclenchent une mort quand le joueur marche dessus.

# 3) Question de design : Boomerang

## Avez-vous défini une classe séparée pour gérer le boomerang, et si oui, étend-elle une classe de sprite ? Pourquoi ?

`Boomerang`est une classe séparée définie dans `weapons.py`. Elle hérite de `Weapon`, qui hérite elle-même de `arcade.TextureAnimationSprite`. Le boomerang est donc un sprite animé Arcade, comme les autres éléments visibles du jeu.

C’est pratique car le boomerang a besoin d’une position, d’une animation, d’une visibilité, d’un déplacement et de collisions. Toute la logique du boomerang est regroupée dans sa classe : lancement, retour, vitesse, distance maximale et collisions avec les ennemis ou les murs. `GameView` se contente surtout de créer le boomerang, de l’afficher et d’appeler `update_boomerang`.

## Comment gérez-vous les 3 états du boomerang ?

Les trois états du boomerang sont gérés avec l’énumération `BoomerangState`, définie dans `weapons.py`. Elle contient `INACTIVE`, `LAUNCHING` et `RETURNING`.

Au début, le boomerang est `INACTIVE`, donc invisible. Quand le joueur appuie sur `D`, la méthode `launch` vérifie qu’il est inactif, puis le fait passer en `LAUNCHING`. Dans cet état, il avance en ligne droite jusqu’à toucher un mur, atteindre sa distance maximale ou devoir revenir après un impact. Ensuite, il passe en `RETURNING`, revient vers la position actuelle du joueur, puis repasse en `INACTIVE` quand il est assez proche.


# 4) Question de design : Epée

## Comment gérez-vous le fait que vous avez maintenant deux types d’armes, avec des comportements différents ? Pensez-vous que vous pourriez ajouter une troisième arme sans tout refaire ?

`Boomerang` et `Sword` héritent tous les deux de la classe `Weapon`, définie dans `weapons.py`. Cette classe commune hérite de `arcade.TextureAnimationSprite`, donc les deux armes sont des sprites animés avec une position, une visibilité et des collisions.

Chaque arme garde ensuite son propre comportement : le `Boomerang` gère ses états avec `BoomerangState` et revient vers le joueur, tandis que `Sword` gère une attaque courte avec une animation selon la direction du joueur. Dans `GameView`, l’arme active est stockée avec `active_weapon`, qui peut valoir `WeaponType.BOOMERANG` ou `WeaponType.SWORD`. Quand le joueur appuie sur `R`, l’arme active change, et quand il appuie sur `D`, le jeu utilise l’arme actuellement sélectionnée.

Pour ajouter une troisième arme, il faudrait créer une nouvelle classe qui hérite de `Weapon`, par exemple `Bow(Weapon)`, avec sa propre méthode d’attaque et de mise à jour. Il faudrait ensuite ajouter cette arme dans `WeaponType` et dans la gestion des touches de `GameView`, mais il ne serait pas nécessaire de refaire tout le système des armes.

## Si un monstre attaque le joueur “par derrière” pendant que l’épée est active, que devrait-il se passer ? Est-ce que votre implémentation a le comportement attendu ?

Dans mon implémentation, l’épée et le joueur restent deux sprites séparés. L’épée peut tuer les monstres qu’elle touche, mais elle ne rend pas le joueur invincible. Donc si un monstre touche le joueur pendant que l’épée est active, même par derrière, la collision joueur-monstre est toujours détectée dans `restart_if_collision`.
Ce comportement est logique : l’épée attaque seulement dans une zone autour du joueur, mais elle ne protège pas automatiquement tout le corps du joueur.

# 5) Question de design : Chauve-Souris

## Comment gérez-vous le fait que vous avez maintenant deux types de monstres, avec des comportements différents ? Pensez-vous que vous pourriez ajouter un troisième monstre sans tout refaire ?

`Bat` et `Blob` héritent d'une classe abstraite `Enemy` qui définit une méthode abstraite `move`. Chaque sous-classe implémente `move` à sa façon. Dans `GameView`, une seule liste `self.enemies` suffit et `on_update` appelle `enemy.move(...)` sans savoir si c'est un `Bat` ou un `Blob`.

Pour ajouter un 3e monstre, il suffit de créer une classe `Ghost(Enemy)` avec sa propre méthode `move` sans toucher à `GameView`.

# 6) Questions de design : Blobs

## Qu’avez-vous choisi comme type de nœud TypeNoeud ? Pourquoi ?

Chaque nœud est un `tuple[float, float]` représentant une position en pixels `(x, y)`. il est hashable(obligé) et il est directement utilisable par NetworkX et par Arcade (`has_line_of_sight`, `dijkstra_path`). Pas besoin d’une classe ou d’un dataclass supplémentaire. Si on met des int, cela pose problème quand NAVMESH_DENSITY ne divise pas TILE_SIZE en entier. On a arrondie à la 6ème décimale pour avoir une bonne précistion, si on arrondissait pas, la boucle `"while not path found: "` serait une boucle infini car `pos_target in composante` serait presque tout le temps False.

## À quel niveau traitez-vous la construction du navmesh, et où le stockez-vous ? Pourquoi ces choix ?

Le navmesh est construit dans `map.py` par `_build_navmesh`, appelée depuis `load_map_from_string`, et stocké dans `Map.navmesh`. Ainsi `Map` contient tout ce qui décrit le niveau : la grille, les positions de départ, et le graphe de navigation. `GameView` n’a qu’à lire `self.map.navmesh` sans s’occuper de la construction.

## Pouvez-vous tester la construction du navmesh sans dépendre de Arcade ?

Oui. `_build_navmesh` et `load_map_from_string` ne dépendent que de `networkx` et de `constants` — aucun import Arcade. On peut donc appeler `load_map_from_string(MAP_TEXT)` dans un test unitaire classique (sans fixture `window`) et vérifier le nombre de nœuds, les arêtes, ou un chemin Dijkstra.

## Si vous avez n×n nœuds par cellule et une carte m×m, quelle est la complexité ?

-Construction du navmesh : O(m² × n²),on parcourt chaque case une fois (m×m cases à parcourir donc O(m²)) et on parcour les 9 cases voisines de chaque noeud donc 9×O(n²) = O(n²).

-Recherche de chemin (Dijkstra): NetworkX utilise un tas binaire, la complexité est donc O((|V|+|E|)×log|V|). Dans le navmesh chaque nœud a au plus 8 voisins (4 droits + 4 diagonaux), donc |E| = 8×O(|V|) = O(|V|). Ce qui donne O(2×|V|×log|V|) = O(|V|×log|V|). Avec |V| = m²×n² nœuds au total : O(m²×n²×log(m²×n²)).

-Déplacement du blob(`move`) : Θ(1) par frame on fait des vérifications sur la position du blob en temps constant et on le fait avancé si c'est possible


# 7) Question de design : Interrupteurs et portails

## Quelle structure de données utilisez-vous pour représenter les conditions d’ouverture des portails ? Pourquoi ?

Les conditions d’ouverture des portails sont représentées par un dictionnaire récursif, avec le type `GateCondition` défini dans `gate_conditions.py`.

Une condition est donc gardée presque sous la même forme que dans le YAML. Par exemple, une condition comme `switch_is_on: first` devient un dictionnaire du type `{"switch_is_on": "first"}`, et une condition plus complexe avec `and`, `or` ou `not` contient une liste de sous-conditions. Cette structure est pratique car elle correspond directement à la définition récursive des formules logiques, et la fonction `condition_is_true` peut l’évaluer simplement en s’appelant elle-même sur les sous-formules.

## Pouvez-vous tester l’évaluation des formules logiques sans dépendre de Arcade ?

Oui, l’évaluation des formules logiques peut être testée sans Arcade, car elle est séparée dans le fichier `gate_conditions.py`. La fonction `condition_is_true` prend seulement deux arguments : une condition `GateCondition` et un dictionnaire `switch_states` qui associe chaque id d’interrupteur à `True` ou `False`.

On peut donc tester directement des formules comme `switch_is_on`, `not`, `and` ou `or` avec de simples dictionnaires Python, sans créer de fenêtre Arcade, de sprites ou de `GameView`. C’est utile parce que la logique des portails reste indépendante de l’affichage et du moteur de jeu.

## S’il y a n interrupteurs et m portails, et en supposant que chaque condition de portail n’est qu’un unique switch_is_on, quelle est la complexité de traitement des portails à chaque frame ?

À chaque frame, `GameView` appelle `update_gate_states`. Cette méthode construit d’abord un dictionnaire `switch_states` avec l’état de tous les interrupteurs, ce qui coûte `Θ(n)`.

Ensuite, elle parcourt les `m` portails. Pour chaque portail, si la condition est seulement un `switch_is_on`, l’évaluation est en `Θ(1)` grâce au dictionnaire des interrupteurs. Le traitement des portails coûte donc `Θ(m)`.

Au total, la complexité par frame est donc `Θ(n + m)`.

# 8) Analyse des performances

## Chargement de la map - facteur choisi : NAVMESH_DENSITY

Pour le chargement de la map, le facteur que nous faisons varier est `NAVMESH_DENSITY`, note `n`. Ce facteur indique combien de noeuds de navmesh sont crees sur un cote d'une cellule. Une cellule marchable cree donc au plus `n^2` noeuds.

Si la map a une taille `m x m`, il y a `m^2` cellules a parcourir. Pour chaque cellule marchable, la construction du navmesh essaie de creer `n^2` noeuds. Pour chaque noeud, le code verifie les 9 cellules voisines pour savoir s'il est trop proche d'un buisson. Cette verification reste en `Theta(1)`, car les positions des buissons sont stockees dans un `set`, donc le test `(x, y) in cases_buissons` ne parcourt pas toute la liste des buissons.

Ensuite, le code relie les noeuds voisins. Chaque noeud teste au plus 8 voisins possibles : 4 voisins droits et 4 voisins diagonaux. Ces tests utilisent le dictionnaire `node_positions`, donc la recherche d'un voisin est aussi en `Theta(1)`. Le nombre total d'aretes reste donc proportionnel au nombre de noeuds.

La partie dominante du chargement est donc la construction du navmesh. Avec `m` fixe, si on augmente `n`, le nombre de noeuds augmente comme `n^2`. La complexite grossiere du chargement est donc `Theta(m^2 * n^2)`. Dans le benchmark, `m` est fixe et on fait varier `n`, donc on s'attend a une croissance proche de `Theta(n^2)`.

## Benchmarks - chargement

Le script `benchmark.py` construit une map ouverte de taille fixe `20 x 20`, puis mesure `load_map_from_string` pour plusieurs valeurs de `NAVMESH_DENSITY`. Les mesures brutes sont sauvegardees dans `benchmarks.csv`, et le graphe dans `benchmarks.png`.

| NAVMESH_DENSITY n | Nombre de noeuds | Temps moyen (ms) | Ecart-type (ms) |
|---:|---:|---:|---:|
| 1                 | 324              | 4.007            | 0.754           |
| 2                 | 1156 | 12.534 | 0.837 |
| 3                 | 2704 | 30.162 | 2.156 |
| 4                 | 4624 | 51.272 | 2.750 |
| 5                 | 7396             | 93.032           | 10.483 |
| 7 | 14400 | 172.229 | 13.946 |
| 10 | 29172 | 337.616 | 6.375 |
| 14 | 57188 | 667.680 | 13.174 |

Les resultats suivent bien l'analyse theorique. Quand `n` augmente, le nombre de noeuds augmente fortement, et le temps de chargement augmente de maniere proche de quadratique. Les ecarts ne sont pas parfaitement reguliers, ce qui est normal pour des mesures reelles : il y a le cout de Python, NetworkX, l'allocation memoire, et le systeme d'exploitation.

## on_update - facteur choisi : nombre d'ennemis

Pour `on_update`, le facteur choisi est le nombre d'ennemis, note `k`. C'est un bon facteur car `GameView.do_on_update` appelle `update_enemies`, qui parcourt les spinners puis les ennemis. Dans notre benchmark, on fait varier le nombre de chauves-souris, car leur deplacement est simple et permet d'isoler le cout de la boucle sur les ennemis.

Pour chaque ennemi, `update_enemies` calcule la distance avec le joueur. Ce calcul est en `Theta(1)`. Ensuite, si l'ennemi est assez proche, le code peut appeler `arcade.has_line_of_sight`. Cette fonction depend des murs et de la distance a verifier, mais le spatial hash de `SpriteList` evite de tester tous les murs un par un. Le deplacement d'une chauve-souris est aussi en `Theta(1)` : elle calcule une nouvelle direction eventuelle, puis une nouvelle position.

Dans le cas des blobs, certaines frames peuvent etre plus couteuses, car un blob peut recalculer un chemin avec Dijkstra sur le navmesh. Si `V` est le nombre de noeuds du navmesh, Dijkstra coute environ `Theta((V + E) log V)`. Comme chaque noeud du navmesh a au plus 8 voisins, `E` reste proportionnel a `V`, donc le cout est environ `Theta(V log V)`. Mais ce recalcul n'arrive pas a chaque frame, seulement quand le blob choisit une nouvelle cible ou poursuit le joueur.

Dans le benchmark choisi, avec des chauves-souris, le cout attendu de `on_update` est donc proche de `Theta(k)`. Les autres operations de la frame restent presentes, mais elles ne dependent pas directement du nombre d'ennemis.

## Benchmarks - on_update

Le script `benchmark.py` construit des maps contenant un nombre variable de chauves-souris, cree une `GameView`, puis appelle directement `view.on_update(1 / 60)` sans utiliser `window.test`, comme demande dans la consigne.

| Nombre d'ennemis k | Temps moyen par frame (ms) | Ecart-type (ms) |
|---:|---:|---:|
| 1 | 2.344 | 1.815 |
| 3 | 5.256 | 1.997 |
| 10 | 0.566 | 0.243 |
| 30 | 0.836 | 0.224 |
| 100 | 2.289 | 0.756 |
| 300 | 5.682 | 1.558 |

Les mesures ne sont pas parfaitement monotones pour les petites valeurs de `k`. C'est probablement du au bruit de mesure, aux caches, a Arcade, et aux couts fixes de `on_update` qui dominent quand il y a tres peu d'ennemis. En revanche, pour les valeurs plus grandes, on observe bien que le temps augmente avec le nombre d'ennemis : 30 ennemis coutent moins que 100, et 100 coutent moins que 300. Cela correspond a l'analyse grossiere en `Theta(k)`.

# 9) Extensions personnelles

## Extension 1 : pics intermittents

Une extension ajoutee au jeu est le systeme de pics (`GridCell.SPIKES`, caractere `!` dans la map). Les pics changent regulierement d'etat avec un timer : lorsqu'ils sont actifs, ils sont opaques et tuent le joueur en cas de collision ; lorsqu'ils sont inactifs, ils deviennent semi-transparents et le joueur peut passer dessus sans mourir.

Cette extension est geree dans `interactions.py` avec `update_spikes` et `should_restart_after_spikes_collision`. Elle est testee dans `tests/test_gameplay.py` avec des tests qui verifient le changement d'etat, le changement d'opacite, la mort sur pics actifs et la survie sur pics inactifs.

## Extension 2 : cles, coffres et invincibilite temporaire

Une autre extension est le systeme de cles et de coffres. Les cles sont placees sur la map avec le caractere `k`, les coffres avec `C`. Quand le joueur ramasse une cle, son compteur de cles augmente. Quand il touche un coffre avec au moins une cle, le coffre s'ouvre, consomme une cle, et le joueur devient temporairement indestructible.

Cette extension ajoute un objectif supplementaire au joueur et modifie les interactions avec les ennemis : pendant l'indestructibilite, toucher un ennemi ne redemarre pas la partie, mais retire l'ennemi. Le systeme est integre dans `systems.py` et dans `Player`, et l'affichage du nombre de cles est gere par `text.py`.


