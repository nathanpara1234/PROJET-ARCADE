# --- test_map_parser.py ---
import pytest

from map import GridCell, InvalidMapFileException, load_map_from_string


def test_map_reads_player_start_and_short_lines() -> None:
    """Verifie que le parser lit le depart du joueur et complete les lignes courtes"""
    game_map = load_map_from_string(
"""width: 5
height: 3
---
xxxxx
xP*
xxxxx
---"""
    )

    assert game_map.player_start_x == 1
    assert game_map.player_start_y == 1
    assert game_map.get(2, 1) == GridCell.CRYSTAL
    assert game_map.get(3, 1) == GridCell.GRASS


def test_map_without_player_is_invalid() -> None:
    """Verifie qu'une map sans joueur est refusee"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
"""width: 3
height: 3
---
xxx
x x
xxx
---"""
        )


def test_map_with_two_players_is_invalid() -> None:
    """Verifie qu'une map avec deux departs joueur est refusee"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
"""width: 5
height: 3
---
xxxxx
xPP x
xxxxx
---"""
        )


def test_map_line_too_wide_is_invalid() -> None:
    """Verifie qu'une ligne plus large que les autres est refusee"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
"""width: 3
height: 3
---
xxx
xP x
xxx
---"""
        )


def test_map_unknown_character_is_invalid() -> None:
    """Verifie qu'un caractere inconnu dans la map est refuse"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
"""width: 3
height: 3
---
xxx
x?P
xxx
---"""
        )


# --- test_trou.py ---
from map import GridCell, load_map_from_string


def test_map_reads_separated_holes() -> None:
    """Verifie que deux trous separes sont lus aux bonnes coordonnees"""
    text = """width: 7
height: 5
---
xxxxxxx
x     x
x O O x
x P   x
xxxxxxx
---"""

    game_map = load_map_from_string(text)

    assert game_map.get(2, 2) == GridCell.HOLE
    assert game_map.get(4, 2) == GridCell.HOLE


def test_map_reads_adjacent_holes() -> None:
    """Verifie que deux trous colles sont lus aux bonnes coordonnees"""
    text = """width: 7
height: 5
---
xxxxxxx
x     x
x OO  x
x P   x
xxxxxxx
---"""

    game_map = load_map_from_string(text)

    assert game_map.get(2, 2) == GridCell.HOLE
    assert game_map.get(3, 2) == GridCell.HOLE


# Test Navmesh

import networkx as nx

from constants import NAVMESH_DENSITY, TILE_SIZE
from map import GridCell, load_map_from_string


MAP_SIMPLE = """width: 5
height: 5
---
xxxxx
x   x
x P x
x   x
xxxxx
---"""

MAP_WITH_CENTER_BUSH = """width: 5
height: 5
---
xxxxx
x   x
x xPx
x   x
xxxxx
---"""


def test_navmesh_is_networkx_graph() -> None:
    """Verifie que la map construit un graphe NetworkX pour le navmesh"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert isinstance(game_map.navmesh, nx.Graph)


def test_navmesh_has_nodes() -> None:
    """Verifie que le navmesh contient des noeuds sur les cases marchables"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert len(game_map.navmesh.nodes) > 0


def test_navmesh_has_edges() -> None:
    """Verifie que les noeuds du navmesh sont relies par des aretes"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert len(game_map.navmesh.edges) > 0


def test_navmesh_node_count_is_limited_by_density() -> None:
    """Verifie qu'une case marchable cree au plus NAVMESH_DENSITY carres de noeuds"""
    game_map = load_map_from_string(MAP_SIMPLE)
    walkable_cells = 3 * 3
    max_nodes = walkable_cells * NAVMESH_DENSITY ** 2
    assert len(game_map.navmesh.nodes) <= max_nodes


def test_navmesh_is_connected_on_open_map() -> None:
    """Verifie que le navmesh d'une petite map ouverte est connexe"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert nx.is_connected(game_map.navmesh)


def test_navmesh_edges_have_weight() -> None:
    """Verifie que chaque arete du navmesh possede un poids"""
    game_map = load_map_from_string(MAP_SIMPLE)
    for _, _, data in game_map.navmesh.edges(data=True):
        assert "weight" in data


def test_diagonal_edges_are_heavier_than_straight_edges() -> None:
    """Verifie que les diagonales coutent plus cher que les deplacements droits"""
    game_map = load_map_from_string(MAP_SIMPLE)
    weights = [data["weight"] for _, _, data in game_map.navmesh.edges(data=True)]
    assert min(weights) < max(weights)


def test_dijkstra_finds_navmesh_path() -> None:
    """Verifie que Dijkstra trouve un chemin entre deux noeuds du navmesh"""
    game_map = load_map_from_string(MAP_SIMPLE)
    nodes = list(game_map.navmesh.nodes)
    start = nodes[0]
    end = nodes[-1]
    path = nx.dijkstra_path(game_map.navmesh, start, end)
    assert len(path) >= 2


def test_dijkstra_path_keeps_start_and_end_nodes() -> None:
    """Verifie que le chemin commence et finit sur les bons noeuds"""
    game_map = load_map_from_string(MAP_SIMPLE)
    nodes = list(game_map.navmesh.nodes)
    start = nodes[0]
    end = nodes[-1]
    path = nx.dijkstra_path(game_map.navmesh, start, end)
    assert path[0] == start
    assert path[-1] == end


def test_bush_removes_nearby_navmesh_nodes() -> None:
    """Verifie qu'un buisson reduit le nombre de noeuds proches"""
    map_without_bush = load_map_from_string(MAP_SIMPLE)
    map_with_bush = load_map_from_string(MAP_WITH_CENTER_BUSH)
    assert len(map_with_bush.navmesh.nodes) < len(map_without_bush.navmesh.nodes)


def test_navmesh_nodes_are_not_inside_border_bushes() -> None:
    """Verifie qu'aucun noeud n'est place dans les buissons de bordure"""
    game_map = load_map_from_string(MAP_SIMPLE)
    for x, y in game_map.navmesh.nodes:
        assert x >= TILE_SIZE
        assert y >= TILE_SIZE


def test_map_reads_spikes_cell() -> None:
    """Verifie que le caractere ! est lu comme une case de pics"""
    game_map = load_map_from_string(
"""width: 5
height: 5
---
xxxxx
x ! x
x P x
x   x
xxxxx
---"""
    )

    assert game_map.get(2, 3) == GridCell.SPIKES
