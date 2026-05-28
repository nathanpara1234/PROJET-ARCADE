from dataclasses import dataclass
import csv
from statistics import mean, stdev
from time import perf_counter

import arcade
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import map as map_module
from constants import MAX_WINDOW_HEIGHT, MAX_WINDOW_WIDTH, WINDOW_TITLE
from gameview import GameView
from map import load_map_from_string


LOADING_DENSITIES: list[int] = [1, 2, 3, 4, 5, 7, 10, 14]
ENEMY_COUNTS: list[int] = [1, 3, 10, 30, 100, 300]
LOADING_REPEAT_COUNT = 5
UPDATE_REPEAT_COUNT = 120


@dataclass(frozen=True)
class LoadingResult:
    density: int
    node_count: int
    mean_ms: float
    stdev_ms: float


@dataclass(frozen=True)
class UpdateResult:
    enemy_count: int
    mean_ms: float
    stdev_ms: float


def make_empty_map_text(width: int, height: int) -> str:
    rows: list[str] = []
    for y in range(height - 1, -1, -1):
        if y == 0 or y == height - 1:
            rows.append("x" * width)
        elif y == 1:
            rows.append("xP" + " " * (width - 3) + "x")
        else:
            rows.append("x" + " " * (width - 2) + "x")

    return "width: " + str(width) + "\nheight: " + str(height) + "\n---\n" + "\n".join(rows) + "\n---"


def make_enemy_map_text(enemy_count: int) -> str:
    width = max(20, enemy_count + 4)
    height = 8
    enemy_positions = set(range(2, enemy_count + 2))
    rows: list[str] = []

    for y in range(height - 1, -1, -1):
        if y == 0 or y == height - 1:
            rows.append("x" * width)
        elif y == 1:
            rows.append("xP" + " " * (width - 3) + "x")
        elif y == 5:
            middle = "".join("v" if x in enemy_positions else " " for x in range(1, width - 1))
            rows.append("x" + middle + "x")
        else:
            rows.append("x" + " " * (width - 2) + "x")

    return "width: " + str(width) + "\nheight: " + str(height) + "\n---\n" + "\n".join(rows) + "\n---"


def measure_loading() -> list[LoadingResult]:
    results: list[LoadingResult] = []
    original_density = map_module.NAVMESH_DENSITY
    map_text = make_empty_map_text(20, 20)

    for density in LOADING_DENSITIES:
        map_module.NAVMESH_DENSITY = density
        durations: list[float] = []
        node_count = 0

        for _ in range(LOADING_REPEAT_COUNT):
            start = perf_counter()
            game_map = load_map_from_string(map_text)
            durations.append((perf_counter() - start) * 1000)
            node_count = len(game_map.navmesh.nodes)

        results.append(
            LoadingResult(
                density=density,
                node_count=node_count,
                mean_ms=mean(durations),
                stdev_ms=stdev(durations),
            )
        )

    map_module.NAVMESH_DENSITY = original_density
    return results


def measure_update() -> list[UpdateResult]:
    results: list[UpdateResult] = []
    window = arcade.Window(MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT, WINDOW_TITLE, visible=False)

    try:
        for enemy_count in ENEMY_COUNTS:
            game_map = load_map_from_string(make_enemy_map_text(enemy_count))
            view = GameView(game_map)
            window.show_view(view)

            durations: list[float] = []
            for _ in range(UPDATE_REPEAT_COUNT):
                start = perf_counter()
                view.on_update(1 / 60)
                durations.append((perf_counter() - start) * 1000)

            results.append(
                UpdateResult(
                    enemy_count=enemy_count,
                    mean_ms=mean(durations),
                    stdev_ms=stdev(durations),
                )
            )
    finally:
        window.close()

    return results


def write_csv(loading_results: list[LoadingResult], update_results: list[UpdateResult]) -> None:
    with open("benchmarks.csv", "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["benchmark", "parameter", "node_count", "mean_ms", "stdev_ms"])

        for result in loading_results:
            writer.writerow(
                [
                    "loading_by_navmesh_density",
                    result.density,
                    result.node_count,
                    f"{result.mean_ms:.3f}",
                    f"{result.stdev_ms:.3f}",
                ]
            )

        for result in update_results:
            writer.writerow(
                [
                    "update_by_enemy_count",
                    result.enemy_count,
                    "",
                    f"{result.mean_ms:.3f}",
                    f"{result.stdev_ms:.3f}",
                ]
            )


def draw_graphs(loading_results: list[LoadingResult], update_results: list[UpdateResult]) -> None:
    figure, axes = plt.subplots(1, 2, figsize=(12, 5))

    axes[0].plot(
        [result.density for result in loading_results],
        [result.mean_ms for result in loading_results],
        marker="o",
    )
    axes[0].set_title("Chargement selon NAVMESH_DENSITY")
    axes[0].set_xlabel("NAVMESH_DENSITY")
    axes[0].set_ylabel("Temps moyen (ms)")
    axes[0].grid(True)

    axes[1].plot(
        [result.enemy_count for result in update_results],
        [result.mean_ms for result in update_results],
        marker="o",
    )
    axes[1].set_title("on_update selon le nombre d'ennemis")
    axes[1].set_xlabel("Nombre d'ennemis")
    axes[1].set_ylabel("Temps moyen par frame (ms)")
    axes[1].grid(True)

    figure.tight_layout()
    figure.savefig("benchmarks.png", dpi=150)
    plt.close(figure)


def main() -> None:
    loading_results = measure_loading()
    update_results = measure_update()
    write_csv(loading_results, update_results)
    draw_graphs(loading_results, update_results)
    print("Benchmarks termines: benchmarks.csv et benchmarks.png crees.")


if __name__ == "__main__":
    main()
