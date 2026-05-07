from dataclasses import dataclass
from enum import Enum
from math import sqrt
from typing import Any

import networkx as nx
import yaml

from constants import TILE_SIZE


class InvalidMapFileException(Exception):
    pass


class GridCell(Enum):
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


@dataclass(frozen=True)
class SwitchData:
    # Cette classe ne dessine rien.
    # Elle garde juste les informations lues dans le fichier de map.
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
    open_if: dict[str, Any]


@dataclass(frozen=True)
class SpinnerData:
    x: int
    y: int
    is_horizontal: bool


@dataclass(frozen=True)
class Map:
    width: int
    height: int
    player_start_x: int
    player_start_y: int
    _grid: list[list[GridCell]]
    navmesh: nx.Graph[tuple[float, float]]
    # Les interrupteurs et portails sont stockes dans la Map.
    # GameView les utilisera ensuite pour creer les sprites.
    switches: list[SwitchData]
    gates: list[GateData]

    def get(self, x: int, y: int) -> GridCell:
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            raise IndexError("Coordonnees hors de la map")

        return self._grid[y][x]


def _as_int(value: Any, name: str) -> int:
    # Petit helper pour verifier les valeurs venant du YAML.
    if not isinstance(value, int):
        raise InvalidMapFileException(f"{name} doit etre un entier.")
    return value


def _as_str(value: Any, name: str) -> str:
    # Meme idee que _as_int, mais pour les textes.
    if not isinstance(value, str):
        raise InvalidMapFileException(f"{name} doit etre un texte.")
    return value


def _check_position(x: int, y: int, width: int, height: int) -> None:
    # On evite qu'un switch ou un portail soit place en dehors de la carte.
    if x < 0 or x >= width or y < 0 or y >= height:
        raise InvalidMapFileException("Une position est hors de la carte.")


def _check_formula(formula: Any, switch_ids: set[str]) -> dict[str, Any]:
    # Les conditions des portails sont recursives.
    # Exemple: {"not": [{"switch_is_on": "first"}]}
    if not isinstance(formula, dict) or len(formula) != 1:
        raise InvalidMapFileException("Une condition de portail est invalide.")

    key = next(iter(formula))
    value = formula[key]

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

    return formula


def _read_switches(config: dict[str, Any], width: int, height: int) -> list[SwitchData]:
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

        switch_id = _as_str(switch_dict.get("id"), "id")
        x = _as_int(switch_dict.get("x"), "x")
        y = _as_int(switch_dict.get("y"), "y")
        _check_position(x, y, width, height)

        state = switch_dict.get("state", "off")
        # Si state n'est pas ecrit dans le YAML, l'interrupteur commence off.
        if state != "on" and state != "off":
            raise InvalidMapFileException("L'etat d'un interrupteur doit etre on ou off.")

        if switch_id in used_ids:
            raise InvalidMapFileException("Deux interrupteurs ont le meme id.")

        used_ids.add(switch_id)
        switches.append(SwitchData(switch_id, x, y, state == "on"))

    return switches


def _read_gates(
    config: dict[str, Any],
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

        x = _as_int(gate_dict.get("x"), "x")
        y = _as_int(gate_dict.get("y"), "y")
        _check_position(x, y, width, height)

        # On verifie aussi que la formule open_if est bien ecrite.
        open_if = _check_formula(gate_dict.get("open_if"), switch_ids)
        gates.append(GateData(x, y, open_if))

    return gates


def _node_for_cell(x: int, y: int, i: int, j: int) -> tuple[float, float]:
    node_x = round(x * TILE_SIZE + (2 * i + 1) * TILE_SIZE / 6, 6)
    node_y = round(y * TILE_SIZE + (2 * j + 1) * TILE_SIZE / 6, 6)
    return (node_x, node_y)


def _build_navmesh(grid: list[list[GridCell]], width: int, height: int) -> nx.Graph[tuple[float, float]]:
    graph: nx.Graph[tuple[float, float]] = nx.Graph()
    positions_by_index: dict[tuple[int, int], tuple[float, float]] = {}

    for y in range(height):
        for x in range(width):
            cell = grid[y][x]

            # Les trous, les buissons et les portails sont des obstacles pour les blobs.
            if cell == GridCell.BUSH or cell == GridCell.HOLE or cell == GridCell.GATE:
                continue

            for i in range(3):
                for j in range(3):
                    index = (x * 3 + i, y * 3 + j)
                    position = _node_for_cell(x, y, i, j)
                    positions_by_index[index] = position
                    graph.add_node(position)

    directions = [
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
        (1, 1),
        (-1, 1),
        (1, -1),
        (-1, -1),
    ]

    for index, position in positions_by_index.items():
        x_index, y_index = index

        for dx, dy in directions:
            neighbor_index = (x_index + dx, y_index + dy)
            if neighbor_index in positions_by_index:
                neighbor = positions_by_index[neighbor_index]
                weight = sqrt((neighbor[0] - position[0]) ** 2 + (neighbor[1] - position[1]) ** 2)
                graph.add_edge(position, neighbor, weight=weight)

    return graph


def _load_config(lines: list[str]) -> tuple[dict[str, Any], int]:
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

    return config, separator


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
            elif char == "x":
                row.append(GridCell.BUSH)
            elif char == "*":
                row.append(GridCell.CRYSTAL)
            elif char == "o" or char == "O":
                row.append(GridCell.HOLE)
            elif char == "s":
                row.append(GridCell.SPINNER_HORIZONTAL)
            elif char == "S":
                row.append(GridCell.SPINNER_VERTICAL)
            elif char == "P":
                player_positions.append((x, y_map))
                row.append(GridCell.GRASS)
            elif char == "v":
                row.append(GridCell.BAT)
            elif char == "b":
                row.append(GridCell.BLOB)
            elif char == "^":
                # Le symbole ^ dans le dessin de map veut dire interrupteur.
                row.append(GridCell.SWITCH)
            elif char == "|":
                # Le symbole | dans le dessin de map veut dire portail.
                row.append(GridCell.GATE)
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
        navmesh=_build_navmesh(grid, width, height),
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
