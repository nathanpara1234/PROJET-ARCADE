from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto
from math import sqrt
from textwrap import dedent
from typing import TypeAlias
import networkx as nx
import yaml
from constants import TILE_SIZE, NAVMESH_DENSITY
from gate_conditions import GateCondition

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
    SWITCH = auto()
    GATE = auto()
    KEY = auto()
    CHEST = auto()
    SPIKES = auto()


Grid: TypeAlias = tuple[tuple[GridCell, ...], ...]

@dataclass(frozen=True)
class SwitchData:# un interrupteur a des paramètres qui varient
    id: str
    x: int
    y: int
    is_on: bool

@dataclass(frozen=True)
class GateData:
    x: int
    y: int
    open_if: GateCondition#dictionnaire YAML

@dataclass(frozen=True)
class Map:
    #dimension de la map
    width: int
    height: int
    #position initiale du joueur
    player_start_x: int
    player_start_y: int
    # frozen=True garantit l’immutabilite : ces champs ne peuvent pas etre modifies apres construction
    grid: Grid
    navmesh: nx.Graph[tuple[float, float]]
    switches: tuple[SwitchData, ...]
    gates: tuple[GateData, ...]

    def get(self, x: int, y: int) -> GridCell:#fonction qui retourne le type de la case en (x,y)
        if ((x < 0) or ((x >= self.width) or (y < 0) or (y >= self.height))):#cas impossible
            raise IndexError("Coordonnees hors de la map")

        return self.grid[y][x]#on accède d’abord à la ligne y, puis à la colonne x


# fonctions utilitaires pour valider les types lus depuis le YAML
def as_int(value: object, name: str) -> int: # vérifie si une valeur est un entier
    # YAML peut donner n'importe quel type, ici on exige un entier,
    if not isinstance(value, int):
        raise InvalidMapFileException(f"{name} doit etre un entier.")
    return value

def as_object_dict(value: object, name: str) -> dict[str, object]:
    #verifie qu'une valeur YAML est un dictionnaire a cles string et on retourne si cest vrai

    if not isinstance(value, dict):
        raise InvalidMapFileException("{name} doit etre un dictionnaire.")

    # on reconstruit un dictionnaire de type dict[str, object]
    result: dict[str, object] = {}
    # value.items() donne les couples (cle, valeur)
    item_iterator: Iterator[tuple[object, object]] = iter(value.items())
    for (key, item) in item_iterator:
        # dans le YAML, les cles doivent etre "id", "x", "open_if", etc
        if not isinstance(key, str):
            raise InvalidMapFileException(f"{name} doit avoir des cles texte.")
        # apres ce test, key est une str, donc on peut l'ajouter au resultat
        result[key] = item
    return result

def as_str(value: object, name: str) -> str: # meme idee pour les textes
    # meme logique que as_int: on recoit un object depuis YAML,
    # puis on verifie que c'est bien d'un texte
    if not isinstance(value, str):
        raise InvalidMapFileException(f"{name} doit etre un texte.")
    return value

def exist_value(dictionary: dict[str, object], key: str, name: str) -> object:
    """Recupere une valeur YAML apres avoir verifie que la cle existe"""
    if key not in dictionary:
        raise InvalidMapFileException(f"{name} doit contenir la cle {key}.")
    # une fois la presence verifiee, get(...) recupere la valeur associee.
    return dictionary[key]

def read_yaml_list(config: dict[str, object], section_name: str) -> list[object]:
    '''Lit une section YAML qui doit etre une liste'''
    #on recupere la section demandee dans la config YAML
    # si elle n'existe pas, on considere simplement qu'elle est vide
    if section_name in config:
        section = config[section_name]
    else:
        section = []

    if not isinstance(section, list):
        raise InvalidMapFileException(f"{section_name} doit etre une liste.")

    #on ne connait pas le type exact des elements lus par YAML on créeer donc une list[object]
    result: list[object] = []

    section_iterator: Iterator[object] = iter(section)
    for item in section_iterator:
        result.append(item)
    return result# renvoit la liste de clé

def check_position(x: int, y: int, width: int, height: int) -> None:# vérifie qu'une position est dans la carte
    if x < 0 or x >= width or y < 0 or y >= height:
        raise InvalidMapFileException("Une position est hors de la carte.")

def single_dict_entry(dictionary: dict[str, object], name: str) -> tuple[str, object]:
    #recupere l'unique couple cle-valeur attendu dans une formule YAML
    if len(dictionary) != 1:
        raise InvalidMapFileException(f"{name} doit contenir une seule cle.")

    # comme dans le cours, on cree un iterateur sur les cles du dictionnaire
    key_iterator: Iterator[str] = iter(dictionary)
    key = next(key_iterator)
    value = exist_value(dictionary, key, name)
    return (key, value)


def check_switch_is_on(value: object, switch_ids: set[str]) -> GateCondition:
    #verifie une condition simple: switch_is_on: id
    # exmpl YAML:
    #   switch_is_on: first
    switch_id = as_str(value, "switch_is_on")
    if switch_id not in switch_ids:
        raise InvalidMapFileException("Un portail utilise un interrupteur inconnu.")
    # si tout est valide, on garde la condition
    return {"switch_is_on": switch_id}


def check_not_condition(value: object, switch_ids: set[str]) -> GateCondition:
    #Verifie une condition not, qui contient exactement une sous-condition
    # exmpl YAML:
    #   not:
    #     - switch_is_on: first
    # not inverse une seule condition, donc la liste doit avoir 1 elt
    if not isinstance(value, list) or len(value) != 1:
        raise InvalidMapFileException("not doit contenir une seule condition.")

    # On rappelle check_formula sur la sous-condition:
    # c'est la partie recursive de ce format
    return {"not": [check_formula(value[0], switch_ids)]}


def check_binary_condition(
    operator: str,
    value: object,
    switch_ids: set[str],
) -> GateCondition:
    """Verifie une condition and/or, qui contient exactement deux sous-conditions."""
    # cette fonction sert pour and et or, car ils ont la meme structure ie une liste avec deux conditions à vérifier
    # Exemple YAML:
    #   and:
    #     - switch_is_on: first
    #     - switch_is_on: second
    if not isinstance(value, list) or len(value) != 2:
        raise InvalidMapFileException("and et or doivent contenir deux conditions.")

    # on verifie recursivement les deux sous-conditions
    # elles peuvent elles memes etre des switch_is_on, not, and ou or
    left = check_formula(value[0], switch_ids)
    right = check_formula(value[1], switch_ids)

    # on reconstruit la condition propre avec le meme operateur logique
    if operator == "and":
        return {"and": [left, right]}
    return {"or": [left, right]}


def check_formula(formula: object, switch_ids: set[str]) -> GateCondition:
    """verifie une formule logique de portail lue depuis le YAML"""
    # on commence par verifier que la formule est un dictionnaire YAML
    formula_dict = as_object_dict(formula, "Une condition de portail")

    # une formule doit avoir une seule cle: switch_is_on, not, and ou or.
    (key, value) = single_dict_entry(formula_dict, "Une condition de portail")

    # ensuite on envoie vers la petite fonction specialisee
    if key == "switch_is_on":
        return check_switch_is_on(value, switch_ids)
    if key == "not":
        return check_not_condition(value, switch_ids)
    if key == "and" or key == "or":
        return check_binary_condition(key, value, switch_ids)

    raise InvalidMapFileException("Type de condition inconnu.")

def read_switches(config: dict[str, object], width: int, height: int) -> list[SwitchData]:# On lit la partie "switches:" de la configuration YAML
    # on reutilise la fct commune pour lire et verifier la liste YAML
    switch_config = read_yaml_list(config, "switches")
    switches: list[SwitchData] = []# sert à stocker les interrupteurs lu
    used_ids: set[str] = set()# sert à eviter deux interrupteurs du meme nom

    # iter(...) cree un iterateur sur la liste YAML
    switch_iterator: Iterator[object] = iter(switch_config)
    for switch_value in switch_iterator:# on parcourt ensuite chaque interrupteur
    #et on verifie que chaque element un est un dictionnaire YAML
        # On va ensuite lire l'id, la position et on verifie que celle-ci est dans la map
        switch_dict = as_object_dict(switch_value, "Un interrupteur")
        switch_id = as_str(switch_dict.get("id"), "id")
        x = as_int(switch_dict.get("x"), "x")
        y = as_int(switch_dict.get("y"), "y")
        check_position(x, y, width, height)

        state = switch_dict.get("state", "off")# cherche la valeur de state si pas d'état par défaut on met false
        # PyYAML lit "on" comme True et "off" comme False on doit donce revenir à des str
        if state is True:
            state = "on"
        elif state is False:
            state = "off"

        if state != "on" and state != "off":#on accepte seulement les etats on et off
            raise InvalidMapFileException("L'etat d'un interrupteur doit etre on ou off.")

        if switch_id in used_ids: # deux interrupteurs ne peuvent pas avoir le meme id
            raise InvalidMapFileException("Deux interrupteurs ont le meme id.")

        used_ids.add(switch_id)#on memorise cette id
        switches.append(SwitchData(switch_id, x, y, state == "on"))# et on ajoute un Switchdata et states == veut dire qu'on test l'état du switch

    return switches


def read_gates(config: dict[str, object],width: int,height: int,switches: list[SwitchData],) -> list[GateData]:# On lit la partie "gates:" de la configuration YAML.
    # ici on utilise la meme logique que les interrupteurs
    # On reutilise la meme fct: gates doit aussi etre une liste YAML
    gate_config = read_yaml_list(config, "gates")
    # on regroupe ensuite l'ensemble des ids existants pour pouvoir vérifier les conditions
    switch_ids = {switch.id for switch in switches}
    gates: list[GateData] = []

    gate_iterator: Iterator[object] = iter(gate_config)
    for gate_value in gate_iterator:
        gate_dict = as_object_dict(gate_value, "Un portail")# on verifie d'abord que chaque entree est un dictionnaire
        # on lit ensuite la position du portail depuis le dictionnaire et on vérifie qu'il est dans la map grace à check_position
        x = as_int(gate_dict.get("x"), "x")
        y = as_int(gate_dict.get("y"), "y")
        check_position(x, y, width, height)

        # On verifie aussi que la formule open_if est bien ecrite
        open_if = check_formula(gate_dict.get("open_if"), switch_ids)
        gates.append(GateData(x, y, open_if))

    return gates


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

    # on créé les noeuds sur les cases marchable
    # dans chaque case marchable, on crée NAVMESH_DENSITY à NAVMESH_DENSITY noeuds
    node_positions: dict[tuple[int, int], tuple[float, float]] = {}

    for cell_x, cell_y in cases_marchables:
        for i in range(NAVMESH_DENSITY):
            for j in range(NAVMESH_DENSITY):
                pos = node_for_cell(cell_x, cell_y, i, j)

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

    #on parcours tous les noeuds et on crée les arretes avec tous les voisins
    # on crée deux fois chaque arretes mais cela ne change pas la complexité
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

# puis je vérifie que le résultat est bien un dictionnaire
def load_config(lines: list[str]) -> tuple[dict[str, object], int]:
    # on cherche d'abord le premier separateur --- car tout ce qui est avant est du YAML
    try:
        separator = lines.index("---")
    except ValueError:
        raise InvalidMapFileException("Le separateur --- avant la carte est manquant.")
    # ensuite j'utilise la bibliotheque yaml.safe_load car on ne parse pas le YAML a la main
    try:
        config = yaml.safe_load("\n".join(lines[:separator]))
    except yaml.YAMLError as error:
        raise InvalidMapFileException(f"Configuration YAML invalide: {error}")

    if not isinstance(config, dict):# je vérifie encore que la config est bien un dictionnaire
        raise InvalidMapFileException("La configuration doit etre un dictionnaire YAML.")

    return as_object_dict(config, "La configuration"), separator


def load_map_from_string(text: str) -> Map:
    lines = dedent(text).strip("\n").splitlines()
    if len(lines) < 4:
        raise InvalidMapFileException("Fichier de map incomplet.")

    config, separator = load_config(lines)

    width = as_int(config.get("width"), "width")
    height = as_int(config.get("height"), "height")
    if width <= 0 or height <= 0:
        raise InvalidMapFileException("width et height doivent etre strictement positifs.")

    # on lit d'abord les interrupteurs, puis les portails,
    # car les portails peuvent parler des interrupteurs par leur id.
    switches = read_switches(config, width, height)
    gates = read_gates(config, width, height, switches)

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
            elif char == "O":
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
                row.append(GridCell.SWITCH)
                cases_marchables.append((x, y_map))
            elif char == "|":
                row.append(GridCell.GATE)# on ne le met pas comme case où on peut passer dessus car cela dépend de l'interrupteur
            elif char == "k" :
                row.append(GridCell.KEY)
                cases_marchables.append((x, y_map))
            elif char == "C" :
                row.append(GridCell.CHEST)
                cases_marchables.append((x, y_map))
            elif char == "!":
                row.append(GridCell.SPIKES)
                cases_marchables.append((x, y_map))
            else:
                raise InvalidMapFileException(f"Caractere invalide dans la carte : {char!r}")

        grid.insert(0, row)

    for switch in switches:
        # si le YAML dit qu'il y a un switch ici,
        # on verifie qu'il y a bien un ^ dans le dessin.
        if grid[switch.y][switch.x] != GridCell.SWITCH:
            raise InvalidMapFileException("Un interrupteur doit etre place sur un ^.")

    for gate in gates:# meme verification pour les portails
        if grid[gate.y][gate.x] != GridCell.GATE:
            raise InvalidMapFileException("Un portail doit etre place sur un |.")

    switch_positions = {(switch.x, switch.y) for switch in switches}
    gate_positions = {(gate.x, gate.y) for gate in gates}
    #on verifie l'inverse aussi
    for y in range(height):
        for x in range(width):
            if grid[y][x] == GridCell.SWITCH and (x, y) not in switch_positions:
                # On evite un ^ sans configuration YAML.
                raise InvalidMapFileException("Un ^ doit avoir une configuration switch.")
            if grid[y][x] == GridCell.GATE and (x, y) not in gate_positions:
                # On evite un | sans condition open_if.
                raise InvalidMapFileException("Un | doit avoir une configuration gate.")

    if len(player_positions) != 1:
        raise InvalidMapFileException("La carte doit contenir exactement un P.")

    player_start_x, player_start_y = player_positions[0]

    return Map(
        width=width,
        height=height,
        player_start_x=player_start_x,
        player_start_y=player_start_y,
        grid=tuple(tuple(row) for row in grid),
        navmesh=nx.freeze(build_navmesh(cases_marchables, cases_buissons)),
        switches=tuple(switches),
        gates=tuple(gates),
    )


def load_map_from_file(filename: str) -> Map:
    try:
        with open(filename, "r", encoding="utf-8", newline="\n") as f:
            text = f.read()
    except OSError:
        raise InvalidMapFileException("Impossible de lire le fichier de map.")

    return load_map_from_string(text)
