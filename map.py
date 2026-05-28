from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto
from math import sqrt
import textwrap

import networkx as nx
import yaml

from constants import TILE_SIZE, NAVMESH_DENSITY
from gate_condition import GateCondition


class InvalidMapFileException(Exception):
    pass


class GridCell(Enum):
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
    SWITCH = auto()
    GATE = auto()


@dataclass(frozen=True)
class SwitchData:
    id: str
    x: int
    y: int
    is_on: bool


@dataclass(frozen=True)
class GateData:
    x: int
    y: int
    open_if: GateCondition


def _as_int(value: object, name: str) -> int:
    if not isinstance(value, int):
        raise InvalidMapFileException(f"{name} doit etre un entier.")
    return value


def _as_object_dict(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InvalidMapFileException(f"{name} doit etre un dictionnaire.")
    result: dict[str, object] = {}
    item_iterator: Iterator[tuple[object, object]] = iter(value.items())
    for (key, item) in item_iterator:
        if not isinstance(key, str):
            raise InvalidMapFileException(f"{name} doit avoir des cles texte.")
        result[key] = item
    return result


def exist_value(dictionary: dict[str, object], key: str, name: str) -> object:
    if key not in dictionary:
        raise InvalidMapFileException(f"{name} doit contenir la cle {key}.")
    return dictionary[key]


def _read_yaml_list(config: dict[str, object], section_name: str) -> list[object]:
    section = config.get(section_name, [])
    if section is None:
        return []
    if not isinstance(section, list):
        raise InvalidMapFileException(f"{section_name} doit etre une liste.")
    result: list[object] = []
    section_iterator: Iterator[object] = iter(section)
    for item in section_iterator:
        result.append(item)
    return result


def _as_str(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise InvalidMapFileException(f"{name} doit etre un texte.")
    return value


def _check_position(x: int, y: int, width: int, height: int) -> None:
    if x < 0 or x >= width or y < 0 or y >= height:
        raise InvalidMapFileException("Une position est hors de la carte.")


def _single_dict_entry(dictionary: dict[str, object], name: str) -> tuple[str, object]:
    if len(dictionary) != 1:
        raise InvalidMapFileException(f"{name} doit contenir une seule cle.")
    key_iterator: Iterator[str] = iter(dictionary)
    key = next(key_iterator)
    value = exist_value(dictionary, key, name)
    return (key, value)


def _check_switch_is_on(value: object, switch_ids: set[str]) -> GateCondition:
    switch_id = _as_str(value, "switch_is_on")
    if switch_id not in switch_ids:
        raise InvalidMapFileException("Un portail utilise un interrupteur inconnu.")
    return {"switch_is_on": switch_id}


def _check_not_condition(value: object, switch_ids: set[str]) -> GateCondition:
    if not isinstance(value, list) or len(value) != 1:
        raise InvalidMapFileException("not doit contenir une seule condition.")
    return {"not": [_check_formula(value[0], switch_ids)]}


def _check_binary_condition(operator: str, value: object, switch_ids: set[str]) -> GateCondition:
    if not isinstance(value, list) or len(value) != 2:
        raise InvalidMapFileException("and et or doivent contenir deux conditions.")
    left = _check_formula(value[0], switch_ids)
    right = _check_formula(value[1], switch_ids)
    if operator == "and":
        return {"and": [left, right]}
    return {"or": [left, right]}


def _check_formula(formula: object, switch_ids: set[str]) -> GateCondition:
    formula_dict = _as_object_dict(formula, "Une condition de portail")
    (key, value) = _single_dict_entry(formula_dict, "Une condition de portail")
    if key == "switch_is_on":
        return _check_switch_is_on(value, switch_ids)
    if key == "not":
        return _check_not_condition(value, switch_ids)
    if key == "and" or key == "or":
        return _check_binary_condition(key, value, switch_ids)
    raise InvalidMapFileException("Type de condition inconnu.")


def _read_switches(config: dict[str, object], width: int, height: int) -> list[SwitchData]:
    switch_config = _read_yaml_list(config, "switches")
    switches: list[SwitchData] = []
    used_ids: set[str] = set()
    switch_iterator: Iterator[object] = iter(switch_config)
    for switch_value in switch_iterator:
        switch_dict = _as_object_dict(switch_value, "Un interrupteur")
        switch_id = _as_str(switch_dict.get("id"), "id")
        x = _as_int(switch_dict.get("x"), "x")
        y = _as_int(switch_dict.get("y"), "y")
        _check_position(x, y, width, height)
        state = switch_dict.get("state", "off")
        if state is True:
            state = "on"
        elif state is False:
            state = "off"
        if state != "on" and state != "off":
            raise InvalidMapFileException("L'etat d'un interrupteur doit etre on ou off.")
        if switch_id in used_ids:
            raise InvalidMapFileException("Deux interrupteurs ont le meme id.")
        used_ids.add(switch_id)
        switches.append(SwitchData(switch_id, x, y, state == "on"))
    return switches


def _read_gates(
    config: dict[str, object],
    width: int,
    height: int,
    switches: list[SwitchData],
) -> list[GateData]:
    gate_config = _read_yaml_list(config, "gates")
    switch_ids = {switch.id for switch in switches}
    gates: list[GateData] = []
    gate_iterator: Iterator[object] = iter(gate_config)
    for gate_value in gate_iterator:
        gate_dict = _as_object_dict(gate_value, "Un portail")
        x = _as_int(gate_dict.get("x"), "x")
        y = _as_int(gate_dict.get("y"), "y")
        _check_position(x, y, width, height)
        open_if = _check_formula(gate_dict.get("open_if"), switch_ids)
        gates.append(GateData(x, y, open_if))
    return gates


@dataclass(frozen=True)
class Map:
    width: int
    height: int
    player_start_x: int
    player_start_y: int
    _grid: list[list[GridCell]]
    navmesh: nx.Graph
    switches: list[SwitchData]
    gates: list[GateData]

    def get(self, x: int, y: int) -> GridCell:
        if ((x < 0) or ((x >= self.width) or (y < 0) or (y >= self.height))):
            raise IndexError("Coordonnees hors de la map")
        return self._grid[y][x]


def node_for_cell(x: int, y: int, i: int, j: int) -> tuple[float, float]:
    node_x = round(x * TILE_SIZE + (2 * i + 1) * TILE_SIZE / (2 * NAVMESH_DENSITY), 6)
    node_y = round(y * TILE_SIZE + (2 * j + 1) * TILE_SIZE / (2 * NAVMESH_DENSITY), 6)
    return (node_x, node_y)


def build_navmesh(cases_marchables: list[tuple[int, int]], cases_buissons: set[tuple[int, int]]) -> nx.Graph[tuple[float, float]]:
    step = TILE_SIZE / NAVMESH_DENSITY
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
    raw_lines = text.splitlines()

    sep_indices = [i for i, line in enumerate(raw_lines) if line.strip() == "---"]

    if len(sep_indices) < 1:
        raise InvalidMapFileException("Le separateur --- avant la carte est manquant.")
    if len(sep_indices) < 2:
        raise InvalidMapFileException("Le separateur --- apres la carte est manquant.")

    first_sep = sep_indices[0]
    second_sep = sep_indices[1]

    header_text = textwrap.dedent("\n".join(raw_lines[:first_sep]))
    try:
        config_raw = yaml.safe_load(header_text)
    except yaml.YAMLError:
        raise InvalidMapFileException("Erreur de format YAML dans le header.")

    if config_raw is None:
        config_raw = {}
    if not isinstance(config_raw, dict):
        raise InvalidMapFileException("Le header doit etre un dictionnaire YAML.")

    config: dict[str, object] = {str(k): v for k, v in config_raw.items()}

    if "width" not in config:
        raise InvalidMapFileException("La ligne width est manquante ou mal formee.")
    if "height" not in config:
        raise InvalidMapFileException("La ligne height est manquante ou mal formee.")

    width = _as_int(config["width"], "width")
    height = _as_int(config["height"], "height")

    if width <= 0 or height <= 0:
        raise InvalidMapFileException("width et height doivent etre strictement positifs.")

    switches = _read_switches(config, width, height)
    gates = _read_gates(config, width, height, switches)

    switch_positions = {(s.x, s.y) for s in switches}
    gate_positions = {(g.x, g.y) for g in gates}

    grid_raw_lines = raw_lines[first_sep + 1:second_sep]
    grid_lines = [line.strip() for line in grid_raw_lines]
    while grid_lines and not grid_lines[0]:
        grid_lines.pop(0)

    if len(grid_lines) < height:
        raise InvalidMapFileException("Le nombre de lignes de carte est insuffisant.")

    grid: list[list[GridCell]] = []
    player_positions: list[tuple[int, int]] = []
    cases_marchables: list[tuple[int, int]] = []
    cases_buissons: set[tuple[int, int]] = set()
    found_switch_positions: set[tuple[int, int]] = set()
    found_gate_positions: set[tuple[int, int]] = set()

    for y_in_file in range(height):
        line = grid_lines[y_in_file]

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
            elif char == "^":
                if (x, y_map) not in switch_positions:
                    raise InvalidMapFileException(f"Interrupteur en ({x},{y_map}) sans configuration YAML.")
                row.append(GridCell.SWITCH)
                cases_marchables.append((x, y_map))
                found_switch_positions.add((x, y_map))
            elif char == "|":
                if (x, y_map) not in gate_positions:
                    raise InvalidMapFileException(f"Portail en ({x},{y_map}) sans configuration YAML.")
                row.append(GridCell.GATE)
                found_gate_positions.add((x, y_map))
            else:
                raise InvalidMapFileException(f"Caractere invalide dans la carte : {char!r}")

        grid.insert(0, row)

    if len(player_positions) != 1:
        raise InvalidMapFileException("La carte doit contenir exactement un P.")

    for switch in switches:
        if (switch.x, switch.y) not in found_switch_positions:
            raise InvalidMapFileException(f"L'interrupteur '{switch.id}' n'a pas de caractere ^ dans la carte.")

    for gate in gates:
        if (gate.x, gate.y) not in found_gate_positions:
            raise InvalidMapFileException(f"Un portail n'a pas de caractere | dans la carte.")

    (player_start_x, player_start_y) = player_positions[0]

    return Map(
        width=width,
        height=height,
        player_start_x=player_start_x,
        player_start_y=player_start_y,
        _grid=grid,
        navmesh=build_navmesh(cases_marchables, cases_buissons),
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
