# 1) Question de design : Player

## Comment définissez-vous le type Direction, et pourquoi ?

`Direction` est défini dans `player.py` avec une énumération `Enum`. Elle contient les quatre directions possibles du joueur : `NORTH`, `SOUTH`, `EAST` et `WEST`.

Ce choix permet d'éviter d'utiliser des chaînes de caractères comme `"north"` ou des nombres directement dans le code. Avec une énumération, les valeurs possibles sont limitées et plus lisibles. Par exemple, `Direction.SOUTH` est plus clair que `2` ou `"south"`. Cela aide aussi les vérifications de types, car une direction ne peut être qu'une des quatre valeurs prévues.

La classe `Player` possède un attribut `direction`, initialisé à `Direction.SOUTH`. Cette direction sert à choisir les animations du joueur dans `textures.py`, mais aussi à orienter les attaques dans `weapons.py`. Ainsi, `GameView` ne manipule pas directement des noms de fichiers ou des coordonnées pour savoir où le joueur regarde : elle demande au joueur son état, puis les armes utilisent cet état.

Le fichier `player.py` est donc responsable de l'état du joueur : position, touches pressées, direction, score, clés et invincibilité temporaire. `GameView`, de son côté, reste le point de contact avec Arcade : elle reçoit les événements clavier, appelle les méthodes du joueur, et coordonne les autres systèmes.


## Ces méthodes reçoivent-elles n’importe quel symbol: int, comme dans on_key_press, ou reçoivent-elles un type de données plus spécifique ? Pourquoi ce choix ?

Dans mon implémentation, la méthode `player_move` de la classe `Player` ne reçoit pas directement le `symbol: int` de Arcade. Les touches sont traitées dans `GameView`, dans `on_key_press` et `on_key_release`, puis elles mettent à jour des booléens du joueur comme `up_pressed`, `down_pressed`, `left_pressed` et `right_pressed`.

Ensuite, `player_move` utilise seulement ces booléens pour calculer `change_x`, `change_y` et mettre à jour la direction du joueur. Ce choix sépare mieux les responsabilités : `GameView` s'occupe des événements Arcade, tandis que `Player` s'occupe seulement de son mouvement.

Cette séparation rend aussi le comportement plus simple à tester et à comprendre. Par exemple, si deux touches opposées sont pressées, le joueur peut regarder l'état complet des booléens au lieu de réagir seulement à la dernière touche reçue. Cela évite les bugs classiques où le joueur s'arrête alors qu'une autre touche est encore enfoncée.

# 2) Question de design : Trou
## Comment gérez-vous les trous dans la map et la collision avec le joueur ?

Les trous sont représentés dans `map.py` par la valeur `GridCell.HOLE`. Lors du chargement de la map, le caractère `O` est transformé en case `HOLE`. Le module `map.py` ne crée pas de sprites Arcade : il décrit seulement la carte sous forme abstraite avec une grille de `GridCell`.

Ensuite, `world_builder.py` lit cette `Map` et crée les sprites correspondants. Chaque trou devient un sprite ajouté dans la liste `holes`. Les trous ne sont pas ajoutés à `walls`, car le joueur doit pouvoir marcher dessus. C'est important : un trou n'est pas un mur, c'est une case dangereuse.

À chaque frame, `GameView.do_on_update` appelle `should_restart_after_collision` dans `interactions.py`. Cette fonction vérifie les collisions avec les ennemis, puis calcule la distance entre le joueur et chaque trou. Si le joueur est à une distance inférieure ou égale à 16 pixels du centre d'un trou, `GameView` redémarre la partie avec la méthode `restart`.

La responsabilité est donc découpée ainsi : `map.py` reconnaît les trous dans le fichier texte, `world_builder.py` construit les sprites, `interactions.py` décide si le joueur doit mourir, et `GameView` applique la conséquence en relançant la vue.

# 3) Question de design : Boomerang

## Avez-vous défini une classe séparée pour gérer le boomerang, et si oui, étend-elle une classe de sprite ? Pourquoi ?

`Boomerang` est une classe séparée définie dans `weapons.py`. Elle hérite de `Weapon`, qui hérite elle-même de `arcade.TextureAnimationSprite`. Le boomerang est donc un sprite animé Arcade, comme les autres éléments visibles du jeu.

C'est pratique car le boomerang a besoin d'une position, d'une animation, d'une visibilité, d'un déplacement et de collisions. Toute la logique propre au boomerang est regroupée dans sa classe : lancement, retour, vitesse, distance maximale et collisions avec les ennemis ou les murs.

`GameView` garde le rôle de coordinateur. Elle crée le boomerang, le place dans une `SpriteList`, le dessine, puis appelle `update_boomerang` à chaque frame. Le boomerang connaît son propre comportement, mais il reçoit les éléments nécessaires du jeu, comme le joueur, les murs et les ennemis. Cela évite de mettre tous les calculs de mouvement du boomerang directement dans `GameView`.

## Comment gérez-vous les 3 états du boomerang ?

Les trois états du boomerang sont gérés avec l'énumération `BoomerangState`, définie dans `weapons.py`. Elle contient `INACTIVE`, `LAUNCHING` et `RETURNING`.

Au début, le boomerang est `INACTIVE`, donc invisible. Quand le joueur appuie sur `D` et que l'arme active est le boomerang, `GameView` appelle `boomerang.launch(self.player)`. La méthode `launch` vérifie que le boomerang est inactif, le place sur le joueur, lui donne une vitesse selon la direction du joueur, puis le fait passer en `LAUNCHING`.

Dans l'état `LAUNCHING`, il avance en ligne droite jusqu'à toucher un mur, atteindre sa distance maximale ou toucher un ennemi. Ensuite, il passe en `RETURNING`. Dans cet état, il recalcule sa direction vers la position actuelle du joueur à chaque frame. Quand il revient assez près du joueur, il repasse en `INACTIVE` et disparaît.

Cette organisation correspond à une petite machine à états. Elle évite d'avoir plusieurs booléens difficiles à combiner, comme `is_visible`, `is_returning` et `is_launched`, qui pourraient se contredire.


# 4) Question de design : Epée

## Comment gérez-vous le fait que vous avez maintenant deux types d’armes, avec des comportements différents ? Pensez-vous que vous pourriez ajouter une troisième arme sans tout refaire ?

`Boomerang` et `Sword` héritent tous les deux de la classe `Weapon`, définie dans `weapons.py`. Cette classe commune hérite de `arcade.TextureAnimationSprite`, donc les deux armes sont des sprites animés avec une position, une visibilité et des collisions.

Chaque arme garde ensuite son propre comportement. Le `Boomerang` gère ses états avec `BoomerangState` et revient vers le joueur. `Sword` gère une attaque courte, une durée d'animation, et une texture qui dépend de la direction du joueur. Les deux armes sont donc liées par une structure commune, mais leur logique reste séparée.

Dans `GameView`, l'arme active est stockée avec `active_weapon`, qui peut valoir `WeaponType.BOOMERANG` ou `WeaponType.SWORD`. Quand le joueur appuie sur `R`, l'arme active change. Quand il appuie sur `D`, `GameView` regarde l'arme sélectionnée et appelle soit `boomerang.launch`, soit `sword.attack`.

Pour ajouter une troisième arme, il faudrait créer une nouvelle classe qui hérite de `Weapon`, par exemple `Bow(Weapon)`, avec sa propre méthode d'attaque et de mise à jour. Il faudrait ensuite ajouter cette arme dans `WeaponType` et dans la gestion des touches de `GameView`. Le système n'est pas encore complètement polymorphe, car `GameView` fait encore un `if` sur le type d'arme, mais la base commune `Weapon` limite déjà la duplication.

## Si un monstre attaque le joueur “par derrière” pendant que l’épée est active, que devrait-il se passer ? Est-ce que votre implémentation a le comportement attendu ?

Dans mon implémentation, l'épée et le joueur restent deux sprites séparés. L'épée peut tuer les monstres qu'elle touche, mais elle ne rend pas le joueur invincible. Donc si un monstre touche le joueur pendant que l'épée est active, même par derrière, la collision joueur-monstre est toujours détectée dans `should_restart_after_collision`.

Ce comportement est logique : l'épée attaque dans une zone autour du joueur, mais elle ne protège pas automatiquement tout le corps du joueur. Le seul cas où le joueur peut toucher un ennemi sans perdre est l'extension d'indestructibilité temporaire donnée par les coffres.

# 5) Question de design : Chauve-Souris

## Comment gérez-vous le fait que vous avez maintenant deux types de monstres, avec des comportements différents ? Pensez-vous que vous pourriez ajouter un troisième monstre sans tout refaire ?

`Bat` et `Blob` héritent d'une classe abstraite `Enemy` définie dans `enemies.py`. Cette classe définit une méthode abstraite `move`. Chaque sous-classe implémente `move` à sa façon : la chauve-souris a un mouvement aléatoire dans sa zone, alors que le blob utilise le navmesh pour se déplacer.

Dans `GameView`, les ennemis sont stockés dans `self.enemies`, et les spinners sont aussi conservés dans `self.spinners` car leur mouvement est plus simple et linéaire. Pour les collisions avec le joueur ou les armes, il existe aussi `self.all_enemies`, qui regroupe tous les ennemis dangereux. Cela permet aux armes et au joueur de ne pas devoir savoir précisément quel type d'ennemi est touché.

Le module `systems.py` contient `update_enemies`. Cette fonction parcourt les spinners puis les ennemis, et appelle `enemy.move(...)`. Grâce au polymorphisme, `update_enemies` n'a pas besoin de connaître le détail de chaque sous-classe : Arcade et Python appellent automatiquement la bonne version de `move`.

Pour ajouter un troisième monstre, il suffirait de créer une classe `Ghost(Enemy)` avec sa propre méthode `move`, puis de créer ses sprites dans `world_builder.py` quand la map contient le caractère choisi. Le reste du code pourrait continuer à manipuler ce nouvel ennemi comme un `Enemy`.

# 6) Questions de design : Blobs

## Qu’avez-vous choisi comme type de nœud TypeNoeud ? Pourquoi ?

Chaque nœud est un `tuple[float, float]` représentant une position en pixels `(x, y)`. Ce type est hashable, ce qui est obligatoire pour être utilisé comme nœud dans NetworkX. Il est aussi directement proche de ce dont le jeu a besoin, car les déplacements des blobs se font en positions de pixels.

Je n'ai pas créé de classe spéciale pour les nœuds, car un tuple suffit ici : il représente clairement une position, il est simple à comparer, et il peut être utilisé comme clé dans les dictionnaires internes de NetworkX. Cela garde le navmesh plus léger.

Les valeurs sont des `float`, car avec une densité de navmesh supérieure à 1, les nœuds ne tombent pas toujours sur des coordonnées entières. Les positions sont arrondies pour éviter les problèmes de précision flottante. Sans cela, deux positions qui devraient être identiques pourraient être très légèrement différentes, ce qui casserait les tests d'appartenance dans le graphe.

## À quel niveau traitez-vous la construction du navmesh, et où le stockez-vous ? Pourquoi ces choix ?

Le navmesh est construit dans `map.py` par `build_navmesh`, appelée depuis `load_map_from_string`, et stocké dans `Map.navmesh`. Ainsi, `Map` contient tout ce qui décrit le niveau : la grille, la position de départ du joueur, les interrupteurs, les portails et le graphe de navigation.

Ce choix est logique car le navmesh dépend de la map, pas de l'affichage. Les obstacles utilisés pour le construire sont connus au chargement : buissons, trous et cases non marchables. Comme les portails restent des obstacles pour les blobs même quand ils sont ouverts, le navmesh n'a pas besoin d'être reconstruit pendant le jeu.

`GameView` n'a donc pas à connaître l'algorithme de construction du navmesh. Elle transmet seulement `self.map.navmesh` à `update_enemies`, puis aux blobs. Cela sépare la lecture de la carte, la représentation du monde, et la logique de déplacement.

## Pouvez-vous tester la construction du navmesh sans dépendre de Arcade ?

Oui. `build_navmesh` et `load_map_from_string` ne dépendent pas d'une fenêtre Arcade. On peut donc appeler `load_map_from_string(MAP_TEXT)` dans un test unitaire classique, sans fixture `window`, et vérifier le nombre de nœuds, la présence de certaines arêtes ou l'existence d'un chemin Dijkstra.

C'est un bon choix de design car l'algorithme important du blob peut être testé sans lancer le jeu. Les tests de `tests/test_map.py` peuvent donc vérifier la structure abstraite de la carte, tandis que les tests de gameplay utilisent `GameView` seulement quand il faut tester l'interaction avec Arcade.

## Si vous avez n×n nœuds par cellule et une carte m×m, quelle est la complexité ?

Construction du navmesh : `O(m² × n²)`. On parcourt les `m²` cellules de la map, et chaque cellule marchable peut créer `n²` nœuds. Pour chaque nœud, le code vérifie seulement un nombre constant de voisins ou de cases proches, donc cela ne change pas l'ordre de grandeur.

Recherche de chemin avec Dijkstra : NetworkX utilise un algorithme dont la complexité est environ `O((|V| + |E|) log |V|)`. Dans notre navmesh, chaque nœud a au plus 8 voisins, donc `|E|` est proportionnel à `|V|`. Avec `|V| = m² × n²`, cela donne environ `O(m² × n² × log(m² × n²))`.

Déplacement du blob : une frame simple est proche de `Θ(1)` si le blob suit déjà un chemin, car il avance seulement vers le prochain point. Par contre, quand il choisit une nouvelle destination ou poursuit le joueur, il peut recalculer un chemin, et cette frame devient plus coûteuse à cause de Dijkstra.


# 7) Question de design : Interrupteurs et portails

## Quelle structure de données utilisez-vous pour représenter les conditions d’ouverture des portails ? Pourquoi ?

Les conditions d'ouverture des portails sont représentées par un dictionnaire récursif, avec le type `GateCondition` défini dans `gate_conditions.py`.

Une condition est donc gardée presque sous la même forme que dans le YAML. Par exemple, une condition comme `switch_is_on: first` devient un dictionnaire du type `{"switch_is_on": "first"}`, et une condition plus complexe avec `and`, `or` ou `not` contient une liste de sous-conditions. Cette structure correspond directement à la définition récursive des formules logiques.

La fonction `condition_is_true` évalue ensuite la formule en s'appelant elle-même sur les sous-formules. Cela permet de gérer naturellement des conditions imbriquées, comme un `and` dans un `not`, lui-même dans un `or`.

Les données lues depuis le YAML sont vérifiées dans `map.py`. Les interrupteurs sont représentés par `SwitchData`, et les portails par `GateData`. Ces deux dataclasses appartiennent au modèle abstrait de la map : elles ne sont pas encore des sprites. Ensuite, `world_builder.py` transforme ces données en `SwitchSprite` et `GateSprite`, définis dans le même fichier que la construction du monde.

Pendant le jeu, `interactions.py` fait le lien entre les sprites et la logique : les armes peuvent inverser l'état d'un interrupteur, puis `update_gate_states` réévalue les conditions des portails. Si un portail est fermé, il est dans `walls`; s'il est ouvert, il est retiré de `walls`, donc le joueur peut passer.

## Pouvez-vous tester l’évaluation des formules logiques sans dépendre de Arcade ?

Oui, l'évaluation des formules logiques peut être testée sans Arcade, car elle est séparée dans le fichier `gate_conditions.py`. La fonction `condition_is_true` prend seulement deux arguments : une condition `GateCondition` et un dictionnaire `switch_states` qui associe chaque id d'interrupteur à `True` ou `False`.

On peut donc tester directement des formules comme `switch_is_on`, `not`, `and` ou `or` avec de simples dictionnaires Python, sans créer de fenêtre Arcade, de sprites ou de `GameView`. C'est utile parce que la logique des portails reste indépendante de l'affichage et du moteur de jeu.

Les tests de map vérifient aussi que les configurations YAML invalides sont refusées : un portail ne peut pas dépendre d'un interrupteur inconnu, un `and` ou un `or` doit avoir deux sous-conditions, et un caractère `|` dans la map doit correspondre à une configuration de portail.

## S’il y a n interrupteurs et m portails, et en supposant que chaque condition de portail n’est qu’un unique switch_is_on, quelle est la complexité de traitement des portails à chaque frame ?

À chaque frame, `GameView` appelle `update_gate_states`. Cette méthode construit d'abord un dictionnaire `switch_states` avec l'état de tous les interrupteurs, ce qui coûte `Θ(n)`.

Ensuite, elle parcourt les `m` portails. Pour chaque portail, si la condition est seulement un `switch_is_on`, l'évaluation est en `Θ(1)` grâce au dictionnaire des interrupteurs. Le traitement des portails coûte donc `Θ(m)`.

Au total, la complexité par frame est donc `Θ(n + m)`. L'utilisation d'un dictionnaire est importante ici : chercher l'état d'un interrupteur par son id ne demande pas de parcourir toute la liste des interrupteurs.

# 8) Analyse des performances

## Chargement de la map - facteur choisi : NAVMESH_DENSITY

Pour le chargement de la map, le facteur que nous faisons varier est `NAVMESH_DENSITY`, noté `n`. Ce facteur indique combien de nœuds de navmesh sont créés sur un côté d'une cellule. Une cellule marchable crée donc au plus `n²` nœuds.

Si la map a une taille `m x m`, il y a `m²` cellules à parcourir. Pour chaque cellule marchable, la construction du navmesh essaie de créer `n²` nœuds. Pour chaque nœud, le code vérifie les cellules voisines pour savoir s'il est trop proche d'un buisson. Cette vérification reste en `Θ(1)`, car les positions des buissons sont stockées dans un `set`, donc le test `(x, y) in cases_buissons` ne parcourt pas toute la liste des buissons.

Ensuite, le code relie les nœuds voisins. Chaque nœud teste au plus 8 voisins possibles : 4 voisins droits et 4 voisins diagonaux. Ces tests utilisent un dictionnaire de positions, donc la recherche d'un voisin est aussi en `Θ(1)`. Le nombre total d'arêtes reste donc proportionnel au nombre de nœuds.

La partie dominante du chargement est donc la construction du navmesh. Avec `m` fixe, si on augmente `n`, le nombre de nœuds augmente comme `n²`. La complexité grossière du chargement est donc `Θ(m² × n²)`. Dans le benchmark, `m` est fixe et on fait varier `n`, donc on s'attend à une croissance proche de `Θ(n²)`.

## Benchmarks - chargement

Le script `benchmark.py` construit une map ouverte de taille fixe, puis mesure `load_map_from_string` pour plusieurs valeurs de `NAVMESH_DENSITY`. Les mesures brutes sont sauvegardées dans `benchmarks.csv`, et le graphe dans `benchmarks.png`.

| NAVMESH_DENSITY n | Nombre de nœuds | Temps moyen (ms) | Écart-type (ms) |
|---:|---:|---:|---:|
| 1 | 324 | 4.007 | 0.754 |
| 2 | 1156 | 12.534 | 0.837 |
| 3 | 2704 | 30.162 | 2.156 |
| 4 | 4624 | 51.272 | 2.750 |
| 5 | 7396 | 93.032 | 10.483 |
| 7 | 14400 | 172.229 | 13.946 |
| 10 | 29172 | 337.616 | 6.375 |
| 14 | 57188 | 667.680 | 13.174 |

Les résultats suivent bien l'analyse théorique. Quand `n` augmente, le nombre de nœuds augmente fortement, et le temps de chargement augmente de manière proche de quadratique. Les écarts ne sont pas parfaitement réguliers, ce qui est normal pour des mesures réelles : il y a le coût de Python, NetworkX, l'allocation mémoire, et le système d'exploitation.

## on_update - facteur choisi : nombre d'ennemis

Pour `on_update`, le facteur choisi est le nombre d'ennemis, noté `k`. C'est un bon facteur car `GameView.do_on_update` appelle `update_enemies`, qui parcourt les spinners puis les ennemis. Dans notre benchmark, on fait varier le nombre de chauves-souris, car leur déplacement est simple et permet d'isoler le coût de la boucle sur les ennemis.

Pour chaque ennemi, `update_enemies` calcule la distance avec le joueur. Ce calcul est en `Θ(1)`. Ensuite, si l'ennemi est assez proche, le code peut appeler `arcade.has_line_of_sight`. Cette fonction dépend des murs et de la distance à vérifier, mais le spatial hash de `SpriteList` évite de tester tous les murs un par un. Le déplacement d'une chauve-souris est aussi en `Θ(1)` : elle calcule une nouvelle direction éventuelle, puis une nouvelle position.

Dans le cas des blobs, certaines frames peuvent être plus coûteuses, car un blob peut recalculer un chemin avec Dijkstra sur le navmesh. Si `V` est le nombre de nœuds du navmesh, Dijkstra coûte environ `Θ((V + E) log V)`. Comme chaque nœud du navmesh a au plus 8 voisins, `E` reste proportionnel à `V`, donc le coût est environ `Θ(V log V)`. Mais ce recalcul n'arrive pas à chaque frame, seulement quand le blob choisit une nouvelle cible ou poursuit le joueur.

Dans le benchmark choisi, avec des chauves-souris, le coût attendu de `on_update` est donc proche de `Θ(k)`. Les autres opérations de la frame restent présentes, mais elles ne dépendent pas directement du nombre d'ennemis.

## Benchmarks - on_update

Le script `benchmark.py` construit des maps contenant un nombre variable de chauves-souris, crée une `GameView`, puis appelle directement `view.on_update(1 / 60)` sans utiliser `window.test`, comme demandé dans la consigne.

| Nombre d'ennemis k | Temps moyen par frame (ms) | Écart-type (ms) |
|---:|---:|---:|
| 1 | 2.344 | 1.815 |
| 3 | 5.256 | 1.997 |
| 10 | 0.566 | 0.243 |
| 30 | 0.836 | 0.224 |
| 100 | 2.289 | 0.756 |
| 300 | 5.682 | 1.558 |

Les mesures ne sont pas parfaitement monotones pour les petites valeurs de `k`. C'est probablement dû au bruit de mesure, aux caches, à Arcade, et aux coûts fixes de `on_update` qui dominent quand il y a très peu d'ennemis. En revanche, pour les valeurs plus grandes, on observe bien que le temps augmente avec le nombre d'ennemis : 30 ennemis coûtent moins que 100, et 100 coûtent moins que 300. Cela correspond à l'analyse grossière en `Θ(k)`.

# 9) Extensions personnelles

## Extension 1 : pics intermittents

Une extension ajoutée au jeu est le système de pics (`GridCell.SPIKES`, caractère `!` dans la map). Les pics changent régulièrement d'état avec un timer : lorsqu'ils sont actifs, ils sont opaques et tuent le joueur en cas de collision ; lorsqu'ils sont inactifs, ils deviennent semi-transparents et le joueur peut passer dessus sans mourir.

Cette extension montre le lien entre plusieurs fichiers. `map.py` lit le caractère `!`, `world_builder.py` crée les sprites de pics, `GameView` stocke `spikes_timer` et `spikes_are_active`, et `interactions.py` contient `update_spikes` et `should_restart_after_spikes_collision`. Le timer est mis à jour dans `GameView.do_on_update`, puis la collision est vérifiée juste après.

Elle est testée dans `tests/test_gameplay.py` avec des tests qui vérifient le changement d'état, le changement d'opacité, la mort sur pics actifs et la survie sur pics inactifs.

## Extension 2 : cles, coffres et invincibilite temporaire

Une autre extension est le système de clés et de coffres. Les clés sont placées sur la map avec le caractère `k`, les coffres avec `C`. Quand le joueur ramasse une clé, son compteur de clés augmente. Quand il touche un coffre avec au moins une clé, le coffre s'ouvre, consomme une clé, et le joueur devient temporairement indestructible.

Cette extension ajoute un objectif supplémentaire au joueur et modifie les interactions avec les ennemis : pendant l'indestructibilité, toucher un ennemi ne redémarre pas la partie, mais retire l'ennemi. Le compteur de clés et l'état d'indestructibilité sont stockés dans `Player`. Les collisions avec les clés, coffres et cristaux sont regroupées dans `systems.py` avec `update_collectibles`, et l'affichage du nombre de clés est géré par `text.py`.

Cette organisation garde la même logique générale que le reste du projet : `map.py` décrit les cases, `world_builder.py` crée les sprites, `systems.py` met à jour les systèmes de jeu, `interactions.py` contient les règles de collision importantes, et `GameView` coordonne l'ensemble à chaque frame.
