"""
Benchmarks de performance :
  - Chargement de la map en fonction de NAVMESH_DENSITY (n)
  - on_update en fonction du nombre d'ennemis (k)
"""
import sys
import timeit
import statistics
import time

sys.path.insert(0, ".")

import constants
import map as map_module
import matplotlib.pyplot as plt
import arcade
from gameview import GameView


# ── Helpers ───────────────────────────────────────────────────────────────────

MAP_10x10 = """\
width: 12
height: 12
---
xxxxxxxxxxxx
x          x
x          x
x          x
x          x
x    P     x
x          x
x          x
x          x
x          x
x          x
xxxxxxxxxxxx
---
"""


def make_map_k_bats(k: int) -> str:
    """Génère une map carrée assez grande pour placer k chauves-souris."""
    interior = max(10, int((k * 9) ** 0.5) + 2)
    size = interior + 2
    cx, cy = size // 2, size // 2

    lines = ["x" * size]
    bats_placed = 0
    for row in range(1, size - 1):
        line = ["x"]
        for col in range(1, size - 1):
            if row == cy and col == cx:
                line.append("P")
            elif bats_placed < k and (col + row) % 3 == 0:
                line.append("v")
                bats_placed += 1
            else:
                line.append(" ")
        line.append("x")
        lines.append("".join(line))
    lines.append("x" * size)

    grid = "\n".join(lines)
    return f"width: {size}\nheight: {size}\n---\n{grid}\n---\n"


def measure(fn, number: int = 100) -> tuple[float, float]:
    """Retourne (moyenne en ms, écart-type en ms) sur `number` répétitions."""
    times = []
    for _ in range(number):
        t = timeit.timeit(fn, number=1) * 1000  # en ms
        times.append(t)
    return statistics.mean(times), statistics.stdev(times)


# ── Benchmark 1 : chargement — facteur n (NAVMESH_DENSITY) ───────────────────

N_VALUES   = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20]
load_means: list[float] = []
load_stds:  list[float] = []
load_nodes: list[int]   = []

print("=== Benchmark chargement (facteur n) ===")
for n in N_VALUES:
    constants.NAVMESH_DENSITY = n
    map_module.NAVMESH_DENSITY = n

    reps = max(10, 200 // (n * n + 1))
    mean, std = measure(lambda: map_module.load_map_from_string(MAP_10x10), number=reps)

    gm = map_module.load_map_from_string(MAP_10x10)
    load_means.append(mean)
    load_stds.append(std)
    load_nodes.append(len(gm.navmesh.nodes))
    print(f"  n={n:2d} : {len(gm.navmesh.nodes):6d} noeuds -> {mean:.3f} ms ± {std:.3f}")

constants.NAVMESH_DENSITY = 3
map_module.NAVMESH_DENSITY = 3


# ── Benchmark 2 : on_update — facteur k (nombre d'ennemis) ───────────────────

K_VALUES      = [1, 2, 5, 10, 20, 50, 100]
update_means: list[float] = []
update_stds:  list[float] = []
actual_ks:    list[int]   = []

window = arcade.Window(800, 600, "Benchmark", antialiasing=False)
window.set_vsync(False)

print("\n=== Benchmark on_update (facteur k) ===")
for k in K_VALUES:
    map_text = make_map_k_bats(k)
    gm = map_module.load_map_from_string(map_text)
    view = GameView(gm)
    window.show_view(view)
    actual_k = len(view.enemies)

    # Chauffe : 30 frames pour stabiliser les caches
    for _ in range(30):
        view.on_update(1 / 60)

    # Mesure : 300 appels individuels -> moyenne + écart-type
    mean, std = measure(lambda: view.on_update(1 / 60), number=300)

    update_means.append(mean)
    update_stds.append(std)
    actual_ks.append(actual_k)
    print(f"  k={actual_k:3d} : {mean:.3f} ms/frame ± {std:.3f}")

window.close()


# ── Graphes ───────────────────────────────────────────────────────────────────

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

# Graphe 1 : chargement vs n
ax1.errorbar(N_VALUES, load_means, yerr=load_stds, fmt="o-", color="steelblue",
             capsize=4, label="mesuré (± écart-type)")
scale1 = load_means[0] / N_VALUES[0] ** 2
ax1.plot(N_VALUES, [scale1 * n ** 2 for n in N_VALUES], "--", color="gray",
         label="Θ(n²) théorique")
ax1.set_xlabel("NAVMESH_DENSITY (n)")
ax1.set_ylabel("Temps (ms)")
ax1.set_title("Chargement — facteur n\n(map 10×10 fixe)")
ax1.legend()
ax1.grid(True, alpha=0.3)

# Graphe 2 : on_update vs k
ax2.errorbar(actual_ks, update_means, yerr=update_stds, fmt="o-", color="darkorange",
             capsize=4, label="mesuré (± écart-type)")
scale2 = update_means[0] / actual_ks[0]
ax2.plot(actual_ks, [scale2 * k for k in actual_ks], "--", color="gray",
         label="Θ(k) théorique")
ax2.set_xlabel("Nombre d'ennemis (k)")
ax2.set_ylabel("Temps moyen par frame (ms)")
ax2.set_title("on_update — facteur k\n(chauves-souris)")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("benchmarks.png", dpi=150)
plt.show()
print("\nGraphes sauvegardés dans benchmarks.png")
