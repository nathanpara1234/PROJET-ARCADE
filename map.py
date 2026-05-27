from dataclasses import dataclass
from enum import Enum, auto
from math import sqrt

import networkx as nx

from constants import TILE_SIZE, NAVMESH_DENSITY

class InvalidMapFileException(Exception):#je creer une exception speciale car dans
    #la consigne on disait en cas derreur de format lever une InvalidMapFileException
    pass

class GridCell(Enum):#car la map est une grille de cellules et chaque cellule peut avoir un type
    #ici cest pratique car au lieu de tester case==Y on teste juste GridCell.X
    GRASS = auto()
    BUSH = auto()
    CRYSTAL = auto()
    SPINNER_HORIZONTAL = auto()
    SPINNER_VERTICAL = auto()
    HOLE = auto()
    BAT = auto()
    BLOB = auto()
    KEY = auto()
    CHEST = auto()
    SPIKES = auto()


@dataclass(frozen=True)
class Map:
    #dimension de la map
    width: int
    height: int
    #position initiale du joueur
    player_start_x: int
    player_start_y: int
    _grid: list[list[GridCell]]
    navmesh: nx.Graph

    def get(self, x: int, y: int) -> GridCell:#fonction qui retourne le type de la case en (x,y)
        if ((x < 0) or ((x >= self.width) or (y < 0) or (y >= self.height))):#cas impossible
            raise IndexError("Coordonnees hors de la map")

        return self._grid[y][x]#on accède d'abord à la ligne y, puis à la colonne x


# fonction qui calcule la position d'un noeud dans une case
def node_for_cell(x: int, y: int, i: int, j: int) -> tuple[float, float]:
    node_x = round(x * TILE_SIZE + (2 * i + 1) * TILE_SIZE / (2 * NAVMESH_DENSITY), 6)
    node_y = round(y * TILE_SIZE + (2 * j + 1) * TILE_SIZE / (2 * NAVMESH_DENSITY), 6)
    return (node_x, node_y)


def build_navmesh(cases_marchables: list[tuple[int, int]], cases_buissons: set[tuple[int, int]]) -> nx.Graph[tuple[float, float]]:
    '''1)  on crée les noeuds
    Pour chaque case marchable, on crée n*n noeuds
    Pour chaque noeud, on regarde les 9 cases autour de sa case (voisines + elle-même).
    Si une case voisine est un buisson, on calcule le centre pixel de ce buisson.
    Si le noeud est à moins de TILE_SIZE du centre du buisson, on le supprime
    2) on relie les noeuds voisins
    Pour chaque noeud, on relie ses voisins directs (haut, bas, gauche, droite)
    et ses voisins diagonaux, avec un poids qui correspond à la distance'''

    step = TILE_SIZE / NAVMESH_DENSITY   #pour le poid des arrêtes
    step_diag = step * sqrt(2)

    node_positions: dict[tuple[int, int], tuple[float, float]] = {}

    for cell_x, cell_y in cases_marchables:
        for i in range(NAVMESH_DENSITY):
            for j in range(NAVMESH_DENSITY):
                pos = node_for_cell(cell_x, cell_y, i, j)

                trop_proche = False
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        if (cell_x + dx, cell_y + dy) in cases_buissons:
                            centre_x = (cell_x + dx) * TILE_SIZE + TILE_SIZE // 2
                            centre_y = (cell_y + dy) * TILE_SIZE + TILE_SIZE // 2
                            if sqrt((pos[0] - centre_x) ** 2 + (pos[1] - centre_y) ** 2) < 1 * TILE_SIZE:
                                trop_proche = True
                if trop_proche:
                    continue
                index = (cell_x * NAVMESH_DENSITY + i, cell_y * NAVMESH_DENSITY + j)
                node_positions[index] = pos

    graph: nx.Graph[tuple[float, float]] = nx.Graph()
    graph.add_nodes_from(node_positions.values())

    for index in node_positions:
        xi, yi = index
        pos = node_positions[index]

        voisins_droits = [(xi + 1, yi), (xi - 1, yi), (xi, yi + 1), (xi, yi - 1)]
        for voisin in voisins_droits:
            if voisin in node_positions:
                graph.add_edge(pos, node_positions[voisin], weight=step)

        voisins_diagonaux = [(xi + 1, yi + 1), (xi - 1, yi + 1), (xi + 1, yi - 1), (xi - 1, yi - 1)]
        for voisin in voisins_diagonaux:
            if voisin in node_positions:
                graph.add_edge(pos, node_positions[voisin], weight=step_diag)

    return graph


def load_map_from_string(text: str) -> Map:
    lines = text.splitlines()
    if len(lines) < 4:
        raise InvalidMapFileException("Fichier de map incomplet.")

    width_line = lines[0]
    height_line = lines[1]

    if not width_line.startswith("width: "):
        raise InvalidMapFileException("La ligne width est manquante ou mal formee.")
    if not height_line.startswith("height: "):
        raise InvalidMapFileException("La ligne height est manquante ou mal formee.")

    try:
        width = int(width_line.removeprefix("width: "))
        height = int(height_line.removeprefix("height: "))
    except ValueError:
        raise InvalidMapFileException("width et height doivent etre des entiers.")

    if width <= 0 or height <= 0:
        raise InvalidMapFileException("width et height doivent etre strictement positifs.")

    if lines[2] != "---":
        raise InvalidMapFileException("Le separateur --- avant la carte est manquant.")

    if len(lines) < 3 + height + 1:
        raise InvalidMapFileException("Le nombre de lignes de carte est insuffisant.")

    if lines[3 + height] != "---":
        raise InvalidMapFileException("Le separateur --- apres la carte est manquant.")

    grid: list[list[GridCell]] = []
    player_positions: list[tuple[int, int]] = []
    cases_marchables: list[tuple[int, int]] = []
    cases_buissons: set[tuple[int, int]] = set()

    for y_in_file in range(height):
        line = lines[3 + y_in_file]

        if len(line) > width:
            raise InvalidMapFileException("Une ligne de la carte depasse la largeur indiquee.")

        row: list[GridCell] = []
        y_map = height - 1 - y_in_file

        for x in range(width):
            char = line[x] if x < len(line) else " "

            if char == " ":
                row.append(GridCell.GRASS)
                cases_marchables.append((x, y_map))
            elif char == "x":
                row.append(GridCell.BUSH)
                cases_buissons.add((x, y_map))
            elif char == "*":
                row.append(GridCell.CRYSTAL)
                cases_marchables.append((x, y_map))
            elif char in ("o", "O"):
                row.append(GridCell.HOLE)
            elif char == "s":
                row.append(GridCell.SPINNER_HORIZONTAL)
                cases_marchables.append((x, y_map))
            elif char == "S":
                row.append(GridCell.SPINNER_VERTICAL)
                cases_marchables.append((x, y_map))
            elif char == "P":
                player_positions.append((x, y_map))
                row.append(GridCell.GRASS)
                cases_marchables.append((x, y_map))
            elif char == "v":
                row.append(GridCell.BAT)
                cases_marchables.append((x, y_map))
            elif char == "b":
                row.append(GridCell.BLOB)
                cases_marchables.append((x, y_map))
            elif char == "k":
                row.append(GridCell.KEY)
                cases_marchables.append((x, y_map))
            elif char == "C":
                row.append(GridCell.CHEST)
                cases_marchables.append((x, y_map))
            elif char == "!":
                row.append(GridCell.SPIKES)
                cases_marchables.append((x, y_map))
            else:
                raise InvalidMapFileException(f"Caractere invalide dans la carte : {char!r}")

        grid.insert(0, row)# insere la ligne row au debut de la list grid

    if len(player_positions) != 1:
        raise InvalidMapFileException("La carte doit contenir exactement un P.")

    (player_start_x, player_start_y) = player_positions[0]

    return Map(
        width=width,
        height=height,
        player_start_x=player_start_x,
        player_start_y=player_start_y,
        _grid=grid,
        navmesh=build_navmesh(cases_marchables, cases_buissons),
    )


def load_map_from_file(filename: str) -> Map:
    try:
        with open(filename, "r", encoding="utf-8", newline="\n") as f:
            text = f.read()
    except OSError:
        raise InvalidMapFileException("Impossible de lire le fichier de map.")

    return load_map_from_string(text)
