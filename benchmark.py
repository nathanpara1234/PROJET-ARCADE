"""Benchmarks pour l'analyse de performance du projet.

Deux facteurs sont mesures:
- le chargement d'une map en fonction de NAVMESH_DENSITY;
- le cout de on_update en fonction du nombre d'ennemis.
"""

from collections.abc import Callable
from dataclasses import dataclass
import csv
import statistics
import timeit

import arcade
import matplotlib.pyplot as plt

import constants
import map as map_module
from gameview import GameView


DEFAULT_NAVMESH_DENSITY = 3
BENCHMARK_CSV = "benchmarks.csv"
BENCHMARK_IMAGE = "benchmarks.png"


@dataclass(frozen=True)
class BenchmarkPoint:
    """Une ligne de resultat de benchmark"""

    # label est le facteur qu'on fait varier:
    # NAVMESH_DENSITY pour le chargement, nombre d'ennemis pour on_update.
    label: int

    # extra sert a garder une information utile en plus.
    # Pour le chargement, on y met le nombre de noeuds du navmesh.
    extra: int

    # Temps moyen et ecart-type en millisecondes.
    mean_ms: float
    std_ms: float


def make_open_map(size: int) -> str:
    """Construit une map carree vide de taille size x size."""
    lines: list[str] = []
    player_y = size // 2
    player_x = size // 2

    # On genere une bordure de buissons pour garder le joueur dans la map.
    # L'interieur reste vide pour que le navmesh puisse se developper librement.
    for y in range(size):
        if y == 0 or y == size - 1:
            lines.append("x" * size)
            continue

        row: list[str] = []
        for x in range(size):
            if x == 0 or x == size - 1:
                row.append("x")
            elif x == player_x and y == player_y:
                row.append("P")
            else:
                row.append(" ")
        lines.append("".join(row))

    grid = "\n".join(lines)
    return f"width: {size}\nheight: {size}\n---\n{grid}\n---\n"


def make_map_with_bats(enemy_count: int) -> str:
    """Construit une map avec enemy_count chauves-souris."""
    # On agrandit la map quand le nombre d'ennemis augmente,
    # pour avoir assez de place pour les placer.
    interior = max(8, int(enemy_count**0.5) * 4 + 4)
    size = interior + 2
    player_y = size // 2
    player_x = size // 2
    placed = 0
    lines: list[str] = []

    for y in range(size):
        if y == 0 or y == size - 1:
            lines.append("x" * size)
            continue

        row: list[str] = []
        for x in range(size):
            if x == 0 or x == size - 1:
                row.append("x")
            elif x == player_x and y == player_y:
                row.append("P")
            elif placed < enemy_count and (x + 2 * y) % 3 == 0:
                # Les chauves-souris sont choisies pour le benchmark on_update
                # car leur mouvement est en temps constant.
                row.append("v")
                placed += 1
            else:
                row.append(" ")
        lines.append("".join(row))

    grid = "\n".join(lines)
    return f"width: {size}\nheight: {size}\n---\n{grid}\n---\n"


def measure(function: Callable[[], object], repetitions: int) -> tuple[float, float]:
    """Mesure une fonction et renvoie moyenne/ecart-type en millisecondes."""
    times: list[float] = []
    for _ in range(repetitions):
        # timeit execute une seule fois la fonction; nous repetons nous-memes
        # pour pouvoir calculer un ecart-type.
        elapsed_ms = timeit.timeit(function, number=1) * 1000
        times.append(elapsed_ms)
    return (statistics.mean(times), statistics.stdev(times))


def benchmark_loading() -> list[BenchmarkPoint]:
    """Mesure le chargement selon NAVMESH_DENSITY."""
    results: list[BenchmarkPoint] = []

    # La map reste fixe: le seul facteur qui varie est NAVMESH_DENSITY.
    map_text = make_open_map(20)
    densities = [1, 2, 3, 4, 5, 7, 10, 14]

    print("=== Chargement de map selon NAVMESH_DENSITY ===")
    for density in densities:
        # NAVMESH_DENSITY est importee dans constants.py et dans map.py.
        # On modifie les deux valeurs pour que le benchmark utilise bien density.
        constants.NAVMESH_DENSITY = density
        map_module.NAVMESH_DENSITY = density

        # Les grandes densites coutent plus cher, donc on reduit un peu
        # le nombre de repetitions pour garder un temps raisonnable.
        repetitions = max(5, 80 // density)
        mean_ms, std_ms = measure(
            lambda: map_module.load_map_from_string(map_text),
            repetitions,
        )

        # On recharge une map pour compter les noeuds du navmesh associe.
        loaded_map = map_module.load_map_from_string(map_text)
        node_count = len(loaded_map.navmesh.nodes)
        results.append(BenchmarkPoint(density, node_count, mean_ms, std_ms))

        print(
            f"n={density:2d}, noeuds={node_count:6d}, "
            f"temps={mean_ms:8.3f} ms +/- {std_ms:.3f}"
        )

    # On restaure la valeur normale pour ne pas laisser le projet modifie.
    constants.NAVMESH_DENSITY = DEFAULT_NAVMESH_DENSITY
    map_module.NAVMESH_DENSITY = DEFAULT_NAVMESH_DENSITY
    return results


def benchmark_update() -> list[BenchmarkPoint]:
    """Mesure on_update selon le nombre d'ennemis."""
    results: list[BenchmarkPoint] = []
    enemy_counts = [1, 3, 10, 30, 100, 300]

    # on_update a besoin d'une vraie Window Arcade, mais on appelle directement
    # view.on_update au lieu de window.test, comme demande dans la consigne.
    window = arcade.Window(800, 600, "Benchmark", antialiasing=False)
    window.set_vsync(False)

    print("\n=== on_update selon le nombre d'ennemis ===")
    try:
        for enemy_count in enemy_counts:
            game_map = map_module.load_map_from_string(make_map_with_bats(enemy_count))
            view = GameView(game_map)
            window.show_view(view)
            actual_count = len(view.enemies)

            # Quelques frames de chauffe evitent de mesurer surtout l'initialisation.
            for _ in range(20):
                view.on_update(1 / 60)

            # On mesure uniquement le cout de on_update pour une frame.
            mean_ms, std_ms = measure(lambda: view.on_update(1 / 60), 200)
            results.append(BenchmarkPoint(actual_count, 0, mean_ms, std_ms))

            print(
                f"k={actual_count:3d}, "
                f"temps={mean_ms:8.3f} ms/frame +/- {std_ms:.3f}"
            )
    finally:
        # Fermer la fenetre evite de laisser une ressource graphique ouverte.
        window.close()

    return results


def write_csv(
    loading_results: list[BenchmarkPoint],
    update_results: list[BenchmarkPoint],
) -> None:
    """Sauvegarde les mesures brutes dans un fichier CSV."""
    with open(BENCHMARK_CSV, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["benchmark", "factor", "extra", "mean_ms", "std_ms"])

        # extra = nombre de noeuds du navmesh.
        for point in loading_results:
            writer.writerow(["loading_density", point.label, point.extra, point.mean_ms, point.std_ms])

        # extra n'est pas utilise pour on_update, donc il vaut 0.
        for point in update_results:
            writer.writerow(["update_enemies", point.label, point.extra, point.mean_ms, point.std_ms])


def draw_graphs(
    loading_results: list[BenchmarkPoint],
    update_results: list[BenchmarkPoint],
) -> None:
    """Dessine les deux graphes demandes dans les consignes."""
    densities = [point.label for point in loading_results]
    load_means = [point.mean_ms for point in loading_results]
    load_stds = [point.std_ms for point in loading_results]

    enemies = [point.label for point in update_results]
    update_means = [point.mean_ms for point in update_results]
    update_stds = [point.std_ms for point in update_results]

    figure, (load_axis, update_axis) = plt.subplots(1, 2, figsize=(13, 5))

    # Graphe 1: mesures reelles du chargement + courbe theorique en n^2.
    load_axis.errorbar(densities, load_means, yerr=load_stds, fmt="o-", capsize=4)
    load_scale = load_means[0] / (densities[0] ** 2)
    load_axis.plot(
        densities,
        [load_scale * density**2 for density in densities],
        "--",
        label="Theta(n^2)",
    )
    load_axis.set_title("Chargement selon NAVMESH_DENSITY")
    load_axis.set_xlabel("NAVMESH_DENSITY")
    load_axis.set_ylabel("Temps moyen (ms)")
    load_axis.grid(True, alpha=0.3)
    load_axis.legend()

    # Graphe 2: mesures reelles de on_update + courbe theorique en k.
    update_axis.errorbar(enemies, update_means, yerr=update_stds, fmt="o-", capsize=4)
    update_scale = update_means[0] / enemies[0]
    update_axis.plot(
        enemies,
        [update_scale * enemy_count for enemy_count in enemies],
        "--",
        label="Theta(k)",
    )
    update_axis.set_title("on_update selon le nombre d'ennemis")
    update_axis.set_xlabel("Nombre d'ennemis")
    update_axis.set_ylabel("Temps moyen par frame (ms)")
    update_axis.grid(True, alpha=0.3)
    update_axis.legend()

    figure.tight_layout()
    figure.savefig(BENCHMARK_IMAGE, dpi=150)
    plt.close(figure)


def main() -> None:
    loading_results = benchmark_loading()
    update_results = benchmark_update()
    write_csv(loading_results, update_results)
    draw_graphs(loading_results, update_results)
    print(f"\nMesures sauvegardees dans {BENCHMARK_CSV}")
    print(f"Graphes sauvegardes dans {BENCHMARK_IMAGE}")


if __name__ == "__main__":
    main()
