# 1) Question de design : Boomerang

## Avez-vous défini une classe séparée pour gérer le boomerang, et si oui, étend-elle une classe de sprite ? Pourquoi ?

`Boomerang`est une classe séparée définie dans `weapons.py`. Elle hérite de `Weapon`, qui hérite elle-même de `arcade.TextureAnimationSprite`. Le boomerang est donc un sprite animé Arcade, comme les autres éléments visibles du jeu.

C’est pratique car le boomerang a besoin d’une position, d’une animation, d’une visibilité, d’un déplacement et de collisions. Toute la logique du boomerang est regroupée dans sa classe : lancement, retour, vitesse, distance maximale et collisions avec les ennemis ou les murs. `GameView` se contente surtout de créer le boomerang, de l’afficher et d’appeler `update_boomerang`.

## Comment gérez-vous les 3 états du boomerang ?

Les trois états du boomerang sont gérés avec l’énumération `BoomerangState`, définie dans `weapons.py`. Elle contient `INACTIVE`, `LAUNCHING` et `RETURNING`.

Au début, le boomerang est `INACTIVE`, donc invisible. Quand le joueur appuie sur `D`, la méthode `launch` vérifie qu’il est inactif, puis le fait passer en `LAUNCHING`. Dans cet état, il avance en ligne droite jusqu’à toucher un mur, atteindre sa distance maximale ou devoir revenir après un impact. Ensuite, il passe en `RETURNING`, revient vers la position actuelle du joueur, puis repasse en `INACTIVE` quand il est assez proche.


# 2) Question de design : Epée

## Comment gérez-vous le fait que vous avez maintenant deux types d’armes, avec des comportements différents ? Pensez-vous que vous pourriez ajouter une troisième arme sans tout refaire ?

`Boomerang` et `Sword` héritent tous les deux de la classe `Weapon`, définie dans `weapons.py`. Cette classe commune hérite de `arcade.TextureAnimationSprite`, donc les deux armes sont des sprites animés avec une position, une visibilité et des collisions.

Chaque arme garde ensuite son propre comportement : le `Boomerang` gère ses états avec `BoomerangState` et revient vers le joueur, tandis que `Sword` gère une attaque courte avec une animation selon la direction du joueur. Dans `GameView`, l’arme active est stockée avec `active_weapon`, qui peut valoir `WeaponType.BOOMERANG` ou `WeaponType.SWORD`. Quand le joueur appuie sur `R`, l’arme active change, et quand il appuie sur `D`, le jeu utilise l’arme actuellement sélectionnée.

Pour ajouter une troisième arme, il faudrait créer une nouvelle classe qui hérite de `Weapon`, par exemple `Bow(Weapon)`, avec sa propre méthode d’attaque et de mise à jour. Il faudrait ensuite ajouter cette arme dans `WeaponType` et dans la gestion des touches de `GameView`, mais il ne serait pas nécessaire de refaire tout le système des armes.

## Si un monstre attaque le joueur “par derrière” pendant que l’épée est active, que devrait-il se passer ? Est-ce que votre implémentation a le comportement attendu ?

Dans mon implémentation, l’épée et le joueur restent deux sprites séparés. L’épée peut tuer les monstres qu’elle touche, mais elle ne rend pas le joueur invincible. Donc si un monstre touche le joueur pendant que l’épée est active, même par derrière, la collision joueur-monstre est toujours détectée dans `restart_if_collision`.

Le comportement actuel est donc que le joueur meurt quand même si un monstre le touche pendant l’attaque, sauf s’il est dans l’état `indestructible` obtenu avec un coffre. Ce comportement est logique : l’épée attaque seulement dans une zone autour du joueur, mais elle ne protège pas automatiquement tout le corps du joueur.

# 3) Question de design : Chauve-Souris

## Comment gérez-vous le fait que vous avez maintenant deux types de monstres, avec des comportements différents ? Pensez-vous que vous pourriez ajouter un troisième monstre sans tout refaire ?

---

`Bat` et `Blob` héritent d'une classe abstraite `Enemy` qui définit une méthode abstraite `move`. Chaque sous-classe implémente `move` à sa façon. Dans `GameView`, une seule liste `self.enemies` suffit et `on_update` appelle `enemy.move(...)` sans savoir si c'est un `Bat` ou un `Blob`.

Pour ajouter un 3e monstre, il suffit de créer une classe `Ghost(Enemy)` avec sa propre méthode `move` — sans toucher à `GameView`.

# 4) Questions de design : Blobs

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


# 5) Question de design : Interrupteurs et portails

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

# 6) Analyse des performances

## Chargement de la map — facteur : NAVMESH_DENSITY (n nœuds par côté de cellule)

La partie intéressante du chargement de la map est la construction du navmesh.(le reste est trivial)

Pour une map de m×m cases marchables, on crée n² nœuds par case, soit m²×n² nœuds au total. Pour chaque nœud, on vérifie les 9 cases voisines pour détecter les buissons proches : chaque vérification est Θ(1) grâce au `set` de cases buissons (`(cell_x + dx, cell_y + dy) in cases_buissons`). Sans le `set`, il faudrait parcourir toute la liste des buissons à chaque fois. Ensuite on insère le noeud en  Θ(1) dans le dictionnaire `node_positions`.

La création des arêtes parcourt aussi les m²×n² nœuds. Pour chaque nœud, on cherche ses 8 voisins par des calculs simples et un une recherche Θ(1) dans le dictionnaire.

La complexité totale du chargement est donc Θ(m²×n²). Si on double la densité n, le temps de chargement est multiplié par 4.

### Benchmarks — chargement

| Taille map | n (NAVMESH_DENSITY) | Nœuds | Temps (ms) |
|---|---|---|---|
| 5×5 cases marchables | 3 | — | — |
| 10×10 cases marchables | 3 | — | — |
| 14×14 cases marchables | 3 | — | — |

---

## on_update — facteur : nombre d'ennemis (k)

À chaque frame, `on_update` fait plusieurs choses. La physique, les animations et le déplacement du joueur sont Θ(1). Les collisions joueur/cristaux utilisent un spatial hash : `check_for_collision_with_list` est Θ(1) grâce au hash, indépendamment du nombre de cristaux.

La partie intéressante est la boucle sur les ennemis. Pour chaque ennemi (k ennemis au total), on calcule d'abord la distance joueur/ennemi en Θ(1). Si l'ennemi est assez proche, on appelle `arcade.has_line_of_sight` qui vérifie si il y a des buissons entre le blob et le joueur. Les murs sont dans une `SpriteList` avec spatial hash. La fonction traverse au maximum la diagonale de la map(pire cas), soit Θ(m) cases sur une map de m×m, le spatial hash évite de tester tous les murs, mais pas de parcourir les cases du rayon.

Le déplacement d'une chauve-souris est Θ(1). Le déplacement d'un blob qui suit son chemin est aussi Θ(1). En revanche, quand un blob recalcule un nouveau chemin avec Dijkstra, c'est Θ(m²n² × log(m²n²)) = Θ(m²n²×(log(m)+log(n))) mais ce cas est rare (seulement à l'arrivée à destination).

La complexité de `on_update` est donc Θ(k×m)= Θ(m) dans la majorité des frames. sinon elle est au pire  Θ(k×(m²n²×(log(m)+log(n)))) =  Θ(m²n²×(log(m)+log(n))).

### Benchmarks — on_update

| Nombre d'ennemis (k) | Temps moyen par frame (ms) |
|---|---|
| 1 ennemi | — |
| 5 ennemis | — |
| 10 ennemis | — |
