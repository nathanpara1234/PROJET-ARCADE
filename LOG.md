* [x] Decouverte d'Arcade                                           120
* [x] Lecture et chargement des maps                                180
* [x] Ajout des monstres de base                                    180
* [x] Ajout des trous                                               40
* [x] Ajout des spinners                                            120
* [x] Ajout du boomerang                                            180
* [x] Ajout de l'epee                                               180
* [x] Ajout des chauves-souris                                      150
* [x] Refactoring du code                                           180
* [x] Ajout des blobs                                               180
* [x] Ajout des interrupteurs et portails                           300
* [x] Travail sur les performances et le benchmark                  180
* [x] Ajout des extensions cles/coffres et pics                     180
* [x] Verifier et completer le README.md                            30
* [x] Relire les questions de design                                60
* [x] Corriger les derniers tests                                   120




Semaine 1 Decouverte d'Arcade

On a pris en main Arcade et mis en place la base du jeu : GameView, deplacement du joueur, camera qui suit le joueur. On a aussi cree constants.py et textures.py pour ne pas repeter les valeurs partout et charger les images une seule fois.

Semaine 2  Maps et monstres

(Nathan) fait le chargement des maps depuis un fichier txt avec GridCell en Enum pour representer les types de cases. Nicolas a  fait les spinners avec leurs limites calculées a partir des buissons. On a aussi ajouté la validation du fichier de map avec InvalidMapFileException.

Semaine 3  Trous et boomerang

Nicolas a crée la classe Player qui regroupe tout ce qui concerne le joueur. Il a aussi ajouté les trous (detection par distance plutot que collision) et le boomerang avec ses trois états gérés par un Enum. Nathan a ajouté l'affichage du score avec une deuxième camera fixe.

Semaine 4 Epee et chauves-souris

Nicolas a ajouté l'épée qui hérite de Weapon comme le boomerang, avec l'enum WeaponType pour gérer l'arme active. Nathan a fait les chauves-souris qui se deplacent aléatoirement dans une zone autour de leur position de depart.

Semaine 5  Refactoring et blobs

On a crée la classe abstraite Enemy avec la methode move() pour regrouper Bat et Blob. Nathan a implementé les blobs avec le navmesh et Dijkstra stockés directement dans Map. Nicolas a fait les interrupteurs et portails avec les conditions en YAML et le fichier gate_conditions.py indépendant d'Arcade.

Semaine 6  Tests et interrupteurs

On a complété les tests pytest pour couvrir toutes les fonctionnalités. Nicolas a fini le système de logiques des portails (and, or, not). Nathan a verifié et corrigé les tests sur le navmesh et les blobs.

Semaine 7 - Performances et extensions

Nathan a fait l'extension cles/coffres avec l'invincibilité temporaire. Nicolas a ajouté les pics avec leur alternance actif/inactif. On a aussi fait l'analyse de performances avec le benchmark sur la densité du navmesh et le nombre de blobs.
