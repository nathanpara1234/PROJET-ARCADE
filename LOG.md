# Journal

## Progression

* [x] Creer le LOG.md                                                10
* [x] Decouverte d'Arcade                                           120
* [x] Lecture et chargement des maps                                180
* [x] Ajout des monstres de base                                    180
* [x] Ajout des trous                                               90
* [x] Ajout des spinners                                            120
* [x] Ajout du boomerang                                            180
* [x] Ajout de l'epee                                               180
* [x] Ajout des chauves-souris                                      150
* [x] Refactoring du code                                           180
* [x] Ajout des blobs                                               180
* [x] Ajout des interrupteurs et portails                           240
* [x] Travail sur les performances et le benchmark                  180
* [x] Ajout des extensions cles/coffres et pics                     180
* [ ] Verifier et completer le README.md                            60
* [ ] Relire les questions de design                                60
* [ ] Corriger les derniers tests                                   120

---

## A faire (prochaine etape)

* Nicolas : relire la partie boomerang, epee, interrupteurs/portails et pics dans `Design.md`.
* Nathan : relire la partie monstres, blobs, invincibilite et cles/coffres.
* Groupe : verifier que `README.md`, `LOG.md` et `Design.md` sont coherents avec le code final.

---

## Suivi

### Semaine 1 - Decouverte d'Arcade

Nathan et Nicolas ont decouvert Arcade, la structure generale du projet et les premiers sprites. Le but etait de comprendre comment creer une fenetre, afficher une map simple et commencer a manipuler les objets du jeu.

### Semaine 2 - Maps et monstres

Nathan a travaille sur les premiers monstres et leur integration dans la map. Le projet a commence a utiliser des caracteres dans les fichiers de map pour placer les elements du jeu.

### Semaine 3 - Trous et boomerang

Nicolas a ajoute les trous, qui font recommencer la partie quand le joueur tombe dedans. Il a aussi implemente le boomerang avec ses trois etats : inactif, lancement et retour.

### Semaine 4 - Epee et chauves-souris

Nicolas a ajoute l'epee, le changement d'arme avec la touche `R`, et l'utilisation de l'arme active avec `D`. Nathan a travaille sur les chauves-souris et leur comportement dans le jeu.

### Semaine 5 - Refactoring 1

Nathan et Nicolas ont restructure une partie du code pour mieux separer les responsabilites entre la map, la vue du jeu, les armes, le joueur et les ennemis. Ce refactoring a rendu le projet plus facile a etendre.

### Semaine 6 - Blobs et interrupteurs

Nathan a ajoute les blobs et leur deplacement avec le navmesh. Nicolas a ajoute les interrupteurs et les portails, avec les conditions d'ouverture lues depuis la configuration YAML de la map.

### Semaine 7 - Performances et extensions

Nathan a travaille sur l'invincibilite et l'extension cles/coffres. Nicolas a ajoute les pics animes avec la case `!`, leur alternance entre etat actif et inactif, ainsi que la collision qui relance la partie quand les pics sont dangereux. Le groupe a aussi commence a regarder les performances avec le benchmark.


