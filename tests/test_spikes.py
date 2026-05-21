import networkx as nx

from map import GridCell, load_map_from_string
from constants import TILE_SIZE, NAVMESH_DENSITY

# Map minimale : 3×3 cases marchables entourées de buissons
MAP_SIMPLE = """
    width: 5
    height: 5
    ---
    xxxxx
    x   x
    x P x
    x   x
    xxxxx
    ---
"""

# Map avec un buisson au milieu qui doit bloquer des noeuds
MAP_BUISSON_MILIEU = """
    width: 5
    height: 5
    ---
    xxxxx
    x   x
    x xPx
    x   x
    xxxxx
    ---
"""

# test sur la structure

def test_navmesh_est_un_graphe() -> None:
    """le navmesh est bien un graphe NetworkX"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert isinstance(game_map.navmesh, nx.Graph)


def test_navmesh_a_des_noeuds() -> None:
    """le navmesh contient des noeuds sur les cases marchables"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert len(game_map.navmesh.nodes) > 0


def test_navmesh_a_des_arretes() -> None:
    """les noeuds sont bien reliés entre eux par des arêtes"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert len(game_map.navmesh.edges) > 0


def test_navmesh_noeuds_par_case() -> None:
    """chaque case marchable génère au plus NAVMESH_DENSITY² noeuds"""
    game_map = load_map_from_string(MAP_SIMPLE)
    # 3×3 cases marchables, chacune génère au plus NAVMESH_DENSITY² noeuds
    cases_marchables = 3 * 3
    max_noeuds = cases_marchables * NAVMESH_DENSITY ** 2
    assert len(game_map.navmesh.nodes) <= max_noeuds


def test_navmesh_connexe() -> None:
    """on peut construire un chemin entre n'importe quelle paire de noeuds"""
    game_map = load_map_from_string(MAP_SIMPLE)
    assert nx.is_connected(game_map.navmesh)


# test sur le poids des arrêtes

def test_arretes_ont_un_poids() -> None:
    """toutes les arêtes doivent avoir un attribut weight"""
    game_map = load_map_from_string(MAP_SIMPLE)
    for u, v, data in game_map.navmesh.edges(data=True):
        assert "weight" in data


def test_poids_droits_et_diagonaux() -> None:
    """les arêtes droites doivent avoir un poids inférieur aux arêtes diagonales"""
    game_map = load_map_from_string(MAP_SIMPLE)
    poids = [data["weight"] for _, _, data in game_map.navmesh.edges(data=True)]
    poids_min = min(poids)
    poids_max = max(poids)
    assert poids_min < poids_max


# test de l'algo de dikstra

def test_dijkstra_trouve_un_chemin() -> None:
    """Dijkstra trouve un chemin entre deux noeuds du navmesh"""
    game_map = load_map_from_string(MAP_SIMPLE)
    noeuds = list(game_map.navmesh.nodes)
    depart = noeuds[0]
    arrivee = noeuds[-1]
    chemin = nx.dijkstra_path(game_map.navmesh, depart, arrivee)
    assert len(chemin) >= 2


def test_dijkstra_chemin_commence_et_finit_aux_bonnes_positions() -> None:
    """le chemin de Dijkstra commence et finit aux bons noeuds"""
    game_map = load_map_from_string(MAP_SIMPLE)
    noeuds = list(game_map.navmesh.nodes)
    depart = noeuds[0]
    arrivee = noeuds[-1]
    chemin = nx.dijkstra_path(game_map.navmesh, depart, arrivee)
    assert chemin[0] == depart
    assert chemin[-1] == arrivee


# test pour la proximité des noeuds par rapport aux buissons

def test_buisson_reduit_nombre_noeuds() -> None:
    """un buisson supprime des noeuds proches : la map avec buisson doit avoir moins de noeuds"""
    map_sans = load_map_from_string(MAP_SIMPLE)
    map_avec = load_map_from_string(MAP_BUISSON_MILIEU)
    assert len(map_avec.navmesh.nodes) < len(map_sans.navmesh.nodes)


def test_noeuds_pas_dans_buisson() -> None:
    """aucun noeud du navmesh ne se trouve à l'intérieur d'une case buisson"""
    game_map = load_map_from_string(MAP_SIMPLE)
    # Les buissons de MAP_SIMPLE sont la bordure (colonne 0, 4 et ligne 0, 4)
    for x, y in game_map.navmesh.nodes:
        # Aucun noeud ne doit être dans une case buisson (x < TILE_SIZE ou x > 3*TILE_SIZE)
        assert x >= TILE_SIZE
        assert y >= TILE_SIZE


def test_map_reconnait_les_pics() -> None:
    game_map = load_map_from_string("""width: 5
height: 5
---
xxxxx
x ! x
x P x
x   x
xxxxx
---""")

    assert game_map.get(2, 3) == GridCell.SPIKES
