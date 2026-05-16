# 1) Question de design : gestion des monstres

## Comment gérez-vous le fait que vous avez maintenant deux types de monstres, avec des comportements différents ? Pensez-vous que vous pourriez ajouter un troisième monstre sans tout refaire ?

---

`Bat` et `Blob` héritent d'une classe abstraite `Enemy` qui définit une méthode abstraite `move`. Chaque sous-classe implémente `move` à sa façon. Dans `GameView`, une seule liste `self.enemies` suffit et `on_update` appelle `enemy.move(...)` sans savoir si c'est un `Bat` ou un `Blob`.

Pour ajouter un 3e monstre, il suffit de créer une classe `Ghost(Enemy)` avec sa propre méthode `move` — sans toucher à `GameView`.

# 2) Questions de design :

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


# 3) Analyse des performances

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
