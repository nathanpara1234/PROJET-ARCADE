from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import cast

import networkx as nx
import yaml

from constants import TILE_SIZE, NAVMESH_DENSITY
from gate_conditions import GateCondition


class InvalidMapFileException(Exception):#je creer une exception speciale car dans
    #la consigne on disait en cas derreur de format lever une InvalidMapFileException
    pass


class GridCell(Enum):#car la map est une grille de cellules et chaque cellule peut avoir un type
    #ici cest pratique car au lieu de tester case==Y on teste juste GridCell.X
    GRASS = 0
    BUSH = 1
    CRYSTAL = 2
    SPINNER_HORIZONTAL = 3
    SPINNER_VERTICAL = 4
    HOLE = 5
    BAT = 6
    BLOB = 7
    # Nouvelles cases pour ma partie interrupteurs / portails.
    SWITCH = 8
    GATE = 9
    KEY = 10
    CHEST = 11


@dataclass(frozen=True)
class SwitchData:#création dune dataclass immuable qui stock seulement les données lues dans la map
    id: str
    x: int
    y: int
    is_on: bool


@dataclass(frozen=True)
class GateData:
    # Le portail a une position et une condition pour savoir s'il est ouvert.
    # open_if garde la formule logique lue dans le YAML.
    x: int
    y: int
    open_if: GateCondition#dictionnaire YAML


@dataclass(frozen=True)
class SpinnerData:# stock la position et lorientation d'un spinner
    x: int
    y: int
    is_horizontal: bool


@dataclass(frozen=True)
class Map:#creation de la structure abstraite de la carte (immuable)
    #1. dimension de la map
    width: int
    height: int
    #2. position initiale du joueur
    player_start_x: int
    player_start_y: int
    # 3. grille de cellules qui est une liste de listes
    _grid: list[list[GridCell]]
    # 4. graphe utilisé pour les blobs
    navmesh: nx.Graph[tuple[float, float]]
    # Les interrupteurs et portails sont stockes dans la Map.
    # GameView les utilisera ensuite pour creer les sprites.
    switches: list[SwitchData]
    gates: list[GateData]

    def get(self, x: int, y: int) -> GridCell:#fonction qui retourne le type de la case en (x,y)
        if x < 0 or x >= self.width or y < 0 or y >= self.height:#je teste si les coordonnées sont dans la map
            raise IndexError("Coordonnees hors de la map")

        return self._grid[y][x]#ici dabord y puis x car on accède d’abord à la ligne y, puis à la colonne x
        #sachant que _grid est une liste de lignes


def _as_int(value: object, name: str) -> int:
    # Petit helper pour verifier les valeurs venant du YAML.
    #J’ai créé des petites fonctions helper pour éviter de répéter le même code de vérification.
    if not isinstance(value, int):
        raise InvalidMapFileException(f"{name} doit etre un entier.")
    return value


def _as_str(value: object, name: str) -> str:
    # Meme idee que _as_int, mais pour les textes.
    if not isinstance(value, str):
        raise InvalidMapFileException(f"{name} doit etre un texte.")
    return value


def _check_position(x: int, y: int, width: int, height: int) -> None:
    # On evite qu'un switch ou un portail soit place en dehors de la carte.
    if x < 0 or x >= width or y < 0 or y >= height:
        raise InvalidMapFileException("Une position est hors de la carte.")


def _check_formula(formula: object, switch_ids: set[str]) -> GateCondition:
    # Les conditions des portails sont recursives.
    # Exemple: {"not": [{"switch_is_on": "first"}]}
    if not isinstance(formula, dict) or len(formula) != 1:
        raise InvalidMapFileException("Une condition de portail est invalide.")

    formula_dict = cast(dict[str, object], formula)
    key = next(iter(formula_dict))
    value = formula_dict[key]

    if key == "switch_is_on":
        # Cas de base: on demande l'etat d'un interrupteur par son id.
        switch_id = _as_str(value, "switch_is_on")
        if switch_id not in switch_ids:
            raise InvalidMapFileException("Un portail utilise un interrupteur inconnu.")

    elif key == "not":
        # not contient une seule sous-condition.
        if not isinstance(value, list) or len(value) != 1:
            raise InvalidMapFileException("not doit contenir une seule condition.")
        _check_formula(value[0], switch_ids)

    elif key == "and" or key == "or":
        # and et or contiennent deux sous-conditions.
        if not isinstance(value, list) or len(value) != 2:
            raise InvalidMapFileException("and et or doivent contenir deux conditions.")
        _check_formula(value[0], switch_ids)
        _check_formula(value[1], switch_ids)

    else:
        raise InvalidMapFileException("Type de condition inconnu.")

    return cast(GateCondition, formula_dict)


def _read_switches(config: dict[str, object], width: int, height: int) -> list[SwitchData]:
    # On lit la partie "switches:" de la configuration YAML.
    switch_config = config.get("switches", [])
    if switch_config is None:
        switch_config = []
    if not isinstance(switch_config, list):
        raise InvalidMapFileException("switches doit etre une liste.")

    switches: list[SwitchData] = []
    # used_ids permet de verifier qu'on ne reutilise pas deux fois le meme id.
    used_ids: set[str] = set()

    for switch_dict in switch_config:
        if not isinstance(switch_dict, dict):
            raise InvalidMapFileException("Un interrupteur est invalide.")

        switch_dict = cast(dict[str, object], switch_dict)
        switch_id = _as_str(switch_dict.get("id"), "id")
        x = _as_int(switch_dict.get("x"), "x")
        y = _as_int(switch_dict.get("y"), "y")
        _check_position(x, y, width, height)

        state = switch_dict.get("state", "off")
        # PyYAML lit "on" comme True et "off" comme False.
        if state is True:
            state = "on"
        elif state is False:
            state = "off"

        # Si state n'est pas ecrit dans le YAML, l'interrupteur commence off.
        if state != "on" and state != "off":#on accepte seulement les etats on et off
            raise InvalidMapFileException("L'etat d'un interrupteur doit etre on ou off.")

        if switch_id in used_ids: # deux interrupteurs ne peuvent pas avoir le meme id
            raise InvalidMapFileException("Deux interrupteurs ont le meme id.")

        used_ids.add(switch_id)#on memorise cette id
        switches.append(SwitchData(switch_id, x, y, state == "on"))# et on ajoute un Switchdata

    return switches


def _read_gates(
    config: dict[str, object],
    width: int,
    height: int,
    switches: list[SwitchData],
) -> list[GateData]:
    # On lit la partie "gates:" de la configuration YAML.
    gate_config = config.get("gates", [])
    if gate_config is None:
        gate_config = []
    if not isinstance(gate_config, list):
        raise InvalidMapFileException("gates doit etre une liste.")

    switch_ids = {switch.id for switch in switches}
    gates: list[GateData] = []

    for gate_dict in gate_config:
        if not isinstance(gate_dict, dict):
            raise InvalidMapFileException("Un portail est invalide.")

        gate_dict = cast(dict[str, object], gate_dict)
        x = _as_int(gate_dict.get("x"), "x")
        y = _as_int(gate_dict.get("y"), "y")
        _check_position(x, y, width, height)

        # On verifie aussi que la formule open_if est bien ecrite.
        open_if = _check_formula(gate_dict.get("open_if"), switch_ids)
        gates.append(GateData(x, y, open_if))

    return gates


# fonction qui calcule la position d'un noeud dans une case
def _node_for_cell(x: int, y: int, i: int, j: int) -> tuple[float, float]:
    node_x = round(x * TILE_SIZE + (2 * i + 1) * TILE_SIZE / (2 * NAVMESH_DENSITY), 6)
    node_y = round(y * TILE_SIZE + (2 * j + 1) * TILE_SIZE / (2 * NAVMESH_DENSITY), 6)
    return (node_x, node_y)


def _build_navmesh(cases_marchables: list[tuple[int, int]], cases_buissons: set[tuple[int, int]]) -> nx.Graph[tuple[float, float]]:
    '''1)  on crée les noeuds
    Pour chaque case marchable, on crée n×n noeuds
    Pour chaque noeud, on regarde les 9 cases autour de sa case (voisines + elle-même).
    Si une case voisine est un buisson, on calcule le centre pixel de ce buisson.
    Si le noeud est à moins de TILE_SIZE du centre du buisson, on le supprime
    2) on relie les noeuds voisins
    Pour chaque noeud, on relie ses voisins directs (haut, bas, gauche, droite)
    et ses voisins diagonaux, avec un poids qui correspond à la distance'''

    step      = TILE_SIZE / NAVMESH_DENSITY   #pour le poid des arrêtes
    step_diag = step * sqrt(2)

    # on créé les noeuds sur les cases marchable
    # dans chaque case marchable, on crée NAVMESH_DENSITY × NAVMESH_DENSITY noeuds
    node_positions: dict[tuple[int, int], tuple[float, float]] = {}

    for cell_x, cell_y in cases_marchables:
        for i in range(NAVMESH_DENSITY):
            for j in range(NAVMESH_DENSITY):
                pos = _node_for_cell(cell_x, cell_y, i, j)

                trop_proche = False
                # On parcour les 9 cases autour du noeud (dx et dy valent -1, 0 ou 1) pour toutes les directions
                for dx in range(-1, 2):
                    for dy in range(-1, 2):
                        #on regarde si la case voisine est un buisson
                        if (cell_x + dx, cell_y + dy) in cases_buissons:
                            # Si oui, on calcule le centre pixel de ce buisson
                            centre_x = (cell_x + dx) * TILE_SIZE + TILE_SIZE // 2
                            centre_y = (cell_y + dy) * TILE_SIZE + TILE_SIZE // 2
                            # Si le noeud est trop proche du centre du buisson, on le supprime
                            if sqrt((pos[0] - centre_x) ** 2 + (pos[1] - centre_y) ** 2) < 1 * TILE_SIZE:
                                trop_proche = True
                if trop_proche:
                    continue
                # on crée cet indice pour que la clé ddans le dictionnaire soit en int et pas en float
                index = (cell_x * NAVMESH_DENSITY + i, cell_y * NAVMESH_DENSITY + j)
                node_positions[index] = pos

    graph: nx.Graph[tuple[float, float]] = nx.Graph()
    graph.add_nodes_from(node_positions.values())

    #on parcours tous les noeuds et on créé les arrêtes avec tous les voisins
    # on crée deux fois chaque arrêtes mais cela ne change pas la complexité
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


def _load_config(lines: list[str]) -> tuple[dict[str, object], int]:
    # La partie avant le premier --- est la configuration YAML.
    try:
        separator = lines.index("---")
    except ValueError:
        raise InvalidMapFileException("Le separateur --- avant la carte est manquant.")

    try:
        config = yaml.safe_load("\n".join(lines[:separator]))
    except yaml.YAMLError as error:
        raise InvalidMapFileException(f"Configuration YAML invalide: {error}")

    if not isinstance(config, dict):
        raise InvalidMapFileException("La configuration doit etre un dictionnaire YAML.")

    return cast(dict[str, object], config), separator


def load_map_from_string(text: str) -> Map:
    lines = text.splitlines()
    if len(lines) < 4:
        raise InvalidMapFileException("Fichier de map incomplet.")

    config, separator = _load_config(lines)

    width = _as_int(config.get("width"), "width")
    height = _as_int(config.get("height"), "height")
    if width <= 0 or height <= 0:
        raise InvalidMapFileException("width et height doivent etre strictement positifs.")

    # On lit d'abord les interrupteurs, puis les portails,
    # car les portails peuvent parler des interrupteurs par leur id.
    switches = _read_switches(config, width, height)
    gates = _read_gates(config, width, height, switches)

    map_start = separator + 1
    map_end = map_start + height
    if len(lines) <= map_end:
        raise InvalidMapFileException("Le nombre de lignes de carte est insuffisant.")
    if lines[map_end] != "---":
        raise InvalidMapFileException("Le separateur --- apres la carte est manquant.")

    grid: list[list[GridCell]] = []
    player_positions: list[tuple[int, int]] = []
    cases_marchables: list[tuple[int, int]] = []  # cases où les blobs peuvent aller, donc
    cases_buissons: set[tuple[int, int]] = set()  # positions des buissons pour le check de proximité

    for y_in_file in range(height):
        line = lines[map_start + y_in_file]

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
            elif char == "o" or char == "O":
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
            elif char == "^":
                # Le symbole ^ dans le dessin de map veut dire interrupteur.
                row.append(GridCell.SWITCH)
                cases_marchables.append((x, y_map))
            elif char == "|":
                # Le symbole | dans le dessin de map veut dire portail.
                row.append(GridCell.GATE)
            elif char == "k" :
                row.append(GridCell.KEY)
                cases_marchables.append((x, y_map))
            elif char == "C" :
                row.append(GridCell.CHEST)
                cases_marchables.append((x, y_map))
            else:
                raise InvalidMapFileException(f"Caractere invalide dans la carte : {char!r}")

        grid.insert(0, row)

    for switch in switches:
        # Si le YAML dit qu'il y a un switch ici,
        # on verifie qu'il y a bien un ^ dans le dessin.
        if grid[switch.y][switch.x] != GridCell.SWITCH:
            raise InvalidMapFileException("Un interrupteur doit etre place sur un ^.")

    for gate in gates:
        # Meme verification pour les portails: YAML et dessin doivent correspondre.
        if grid[gate.y][gate.x] != GridCell.GATE:
            raise InvalidMapFileException("Un portail doit etre place sur un |.")

    switch_positions = {(switch.x, switch.y) for switch in switches}
    gate_positions = {(gate.x, gate.y) for gate in gates}

    for y in range(height):
        for x in range(width):
            if grid[y][x] == GridCell.SWITCH and (x, y) not in switch_positions:
                # On evite un ^ sans configuration YAML.
                raise InvalidMapFileException("Un ^ doit avoir une configuration switch.")
            if grid[y][x] == GridCell.GATE and (x, y) not in gate_positions:
                # On evite un | sans condition open_if.
                raise InvalidMapFileException("Un | doit avoir une configuration gate.")

    if len(player_positions) == 0:
        player_positions.append((0, 0))
    elif len(player_positions) != 1:
        raise InvalidMapFileException("La carte doit contenir exactement un P.")

    player_start_x, player_start_y = player_positions[0]

    return Map(
        width=width,
        height=height,
        player_start_x=player_start_x,
        player_start_y=player_start_y,
        _grid=grid,
        navmesh=_build_navmesh(cases_marchables, cases_buissons),
        switches=switches,
        gates=gates,
    )


def load_map_from_file(filename: str) -> Map:
    try:
        with open(filename, "r", encoding="utf-8", newline="\n") as f:
            text = f.read()
    except OSError:
        raise InvalidMapFileException("Impossible de lire le fichier de map.")

    return load_map_from_string(text)


def find_spinners(game_map: Map) -> list[SpinnerData]:
    result: list[SpinnerData] = []

    for y in range(game_map.height):
        for x in range(game_map.width):
            cell = game_map.get(x, y)

            if cell == GridCell.SPINNER_HORIZONTAL:
                result.append(SpinnerData(x=x, y=y, is_horizontal=True))

            elif cell == GridCell.SPINNER_VERTICAL:
                result.append(SpinnerData(x=x, y=y, is_horizontal=False))

    return result
