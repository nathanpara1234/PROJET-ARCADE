import timeit
import matplotlib.pyplot as plt

import map as map_module
import arcade
from constants import MAX_WINDOW_HEIGHT, MAX_WINDOW_WIDTH, WINDOW_TITLE
from gameview import GameView
from map import Map, load_map_from_string


# valeurs de densité testées pour le chargement
DENSITES: list[int] = [1, 2, 3, 4, 5, 7, 10, 14]
# nombre de blobs testés pour on_update
NB_BLOBS_TEST: list[int] = [1, 3, 10, 30, 100, 300]
# on répète 5 fois pour avoir une moyenne stable
NB_REPETITIONS: int = 5
# nombre de frames mesurées pour on_update
NB_FRAMES: int = 300
# frames non mesurées avant le benchmark pour que les blobs aient déjà calculé leur premier chemin
NB_FRAMES_WARMUP: int = 10


# génère une carte vide entourée de buissons avec le joueur en bas à gauche
def make_empty_map(width: int, height: int) -> str:
    lignes: list[str] = []
    for y in range(height - 1, -1, -1):
        if y == 0 or y == height - 1:
            lignes.append("x" * width)
        elif y == 1:
            lignes.append("xP" + " " * (width - 3) + "x")
        else:
            lignes.append("x" + " " * (width - 2) + "x")
    return "width: " + str(width) + "\nheight: " + str(height) + "\n---\n" + "\n".join(lignes) + "\n---"


# génère une carte avec nb_blobs blobs placés sur la ligne y=5
def make_map_blobs(nb_blobs: int) -> str:
    # la carte doit être assez large pour contenir tous les blobs
    width: int = max(20, nb_blobs + 4)
    height: int = 8
    positions_blobs: set[int] = set(range(2, nb_blobs + 2))
    lignes: list[str] = []

    for y in range(height - 1, -1, -1):
        if y == 0 or y == height - 1:
            lignes.append("x" * width)
        elif y == 1:
            lignes.append("xP" + " " * (width - 3) + "x")
        elif y == 5:
            ligne_blobs: str = ""
            for x in range(1, width - 1):
                if x in positions_blobs:
                    ligne_blobs += "b"
                else:
                    ligne_blobs += " "
            lignes.append("x" + ligne_blobs + "x")
        else:
            lignes.append("x" + " " * (width - 2) + "x")

    return "width: " + str(width) + "\nheight: " + str(height) + "\n---\n" + "\n".join(lignes) + "\n---"


def mesurer_chargement() -> list[tuple[int, int, float]]:
    resultats: list[tuple[int, int, float]] = []
    densite_initiale: int = map_module.NAVMESH_DENSITY
    texte_carte: str = make_empty_map(20, 20)

    for densite in DENSITES:
        map_module.NAVMESH_DENSITY = densite

        # on mesure le temps de chargement avec timeit sur NB_REPETITIONS répétitions
        temps_total: float = timeit.timeit(lambda: load_map_from_string(texte_carte), number=NB_REPETITIONS)
        temps_moyen_ms: float = temps_total / NB_REPETITIONS * 1000

        # on charge une fois de plus juste pour compter les noeuds
        carte: Map = load_map_from_string(texte_carte)
        nb_noeuds: int = len(carte.navmesh.nodes)

        resultats.append((densite, nb_noeuds, temps_moyen_ms))

    # on remet la densité d'origine pour ne pas affecter le reste du programme
    map_module.NAVMESH_DENSITY = densite_initiale
    return resultats


def mesurer_update() -> list[tuple[int, float]]:
    resultats: list[tuple[int, float]] = []
    fenetre: arcade.Window = arcade.Window(MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT, WINDOW_TITLE, visible=False)

    for nb_blobs in NB_BLOBS_TEST:
        carte: Map = load_map_from_string(make_map_blobs(nb_blobs))
        vue: GameView = GameView(carte)
        fenetre.show_view(vue)

        # on laisse les blobs calculer leur premier chemin avant de mesurer
        for i in range(NB_FRAMES_WARMUP):
            vue.on_update(1 / 60)

        # on mesure le temps moyen d'une frame sur NB_FRAMES frames
        temps_total: float = timeit.timeit(lambda: vue.on_update(1 / 60), number=NB_FRAMES)
        temps_moyen_ms: float = temps_total / NB_FRAMES * 1000

        resultats.append((nb_blobs, temps_moyen_ms))

    fenetre.close()
    return resultats


def afficher_resultats(resultats_chargement: list[tuple[int, int, float]], resultats_update: list[tuple[int, float]]) -> None:
    print("Chargement (NAVMESH_DENSITY fixé à n, carte 20x20)")
    for resultat in resultats_chargement:
        print("n =", resultat[0], "| nb noeuds =", resultat[1], "| temps moyen =", round(resultat[2], 3), "ms")

    print()
    print("on_update (nombre de blobs k)")
    for resultat in resultats_update:
        print("k =", resultat[0], "| temps moyen =", round(resultat[1], 3), "ms")


def tracer_graphiques(resultats_chargement: list[tuple[int, int, float]], resultats_update: list[tuple[int, float]]) -> None:
    liste_densites: list[int] = []
    temps_chargement: list[float] = []
    for resultat in resultats_chargement:
        liste_densites.append(resultat[0])
        temps_chargement.append(resultat[2])

    liste_nb_blobs: list[int] = []
    temps_update: list[float] = []
    for resultat in resultats_update:
        liste_nb_blobs.append(resultat[0])
        temps_update.append(resultat[1])

    figure, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(liste_densites, temps_chargement, marker="o")
    axes[0].set_title("Chargement selon NAVMESH_DENSITY")
    axes[0].set_xlabel("NAVMESH_DENSITY")
    axes[0].set_ylabel("Temps moyen (ms)")
    axes[0].grid(True)

    axes[1].plot(liste_nb_blobs, temps_update, marker="o")
    axes[1].set_title("on_update selon le nombre de blobs")
    axes[1].set_xlabel("Nombre de blobs")
    axes[1].set_ylabel("Temps moyen par frame (ms)")
    axes[1].grid(True)

    figure.savefig("benchmarks.png")


def main() -> None:
    resultats_chargement: list[tuple[int, int, float]] = mesurer_chargement()
    resultats_update: list[tuple[int, float]] = mesurer_update()
    afficher_resultats(resultats_chargement, resultats_update)
    tracer_graphiques(resultats_chargement, resultats_update)
    print("Graphique sauvegarde dans benchmarks.png")


if __name__ == "__main__":
    main()
