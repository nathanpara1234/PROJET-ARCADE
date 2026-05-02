from constants import TILE_SIZE
from fractions import Fraction
from math import sqrt
import networkx as nx
from dataclasses import dataclass
from enum import Enum
class InvalidMapFileException(Exception):
    pass

class GridCell(Enum):# Sachant qu'il y a que 3 possibilités, on utilise un Enum qui
#est une liste de valeurs possible pour une variable ici 3 choix pour une case de notre map
    GRASS = 0
    BUSH = 1
    CRYSTAL = 2
    SPINNER_HORIZONTAL = 3
    SPINNER_VERTICAL= 4
    HOLE = 5
    BAT = 6
    BLOB = 7


@dataclass(frozen=True) # on rend map immuable on empêche de modifier les attributs
class Map:
    width: int
    height: int
    player_start_x: int
    player_start_y: int
    _grid: list[list[GridCell]]# grille privée contenant les cellules de la map
    navmesh : nx.Graph

    def get(self, x: int, y: int) -> GridCell: #fonction qui sert à savoir ce qu'il y a dans la case et self represente la map actuelle
        if x < 0 or x >= self.width or y < 0 or y >= self.height:# on verifie que la position demandée existe bien dans la map.
            raise IndexError("Coordonnées hors de la map")# si elle existe pas on affiche erreur

        return self._grid[y][x]# on retourne la cellule qui se trouve à la position demandée

# Petite dataclass pratique pour représenter un spinner trouvé sur la map
@dataclass(frozen=True)
class SpinnerData:
    x: int
    y: int
    is_horizontal: bool



# Charge une map depuis une string Python
# Très utile pour les tests

def load_map_from_string(text: str) -> Map:
    G : nx.Graph[tuple[float, float]] = nx.Graph()
    '''def add_central_point (x: int, y: int)->None:
        middle_x = (x * TILE_SIZE) + (TILE_SIZE // 2)
        middle_y = (y * TILE_SIZE) + (TILE_SIZE // 2)
        G.add_node((middle_x, middle_y))'''
    def add_nodes_for_cell(x: int, y: int) -> None:
        for i in range(3):
            for j in range(3):
                node_x = float(Fraction(x * TILE_SIZE * 6 + (2*i+1) * TILE_SIZE, 6))  #node_x = float(Fraction(x * TILE_SIZE * 6 + (2*i+1) * TILE_SIZE, 6))
                node_y = float(Fraction(y * TILE_SIZE * 6 + (2*j+1) * TILE_SIZE, 6))
                node_y = float(Fraction(y * TILE_SIZE * 6 + (2*j+1) * TILE_SIZE, 6))
                G.add_node((node_x, node_y))
        # Le noeud central (i=1, j=1) est toujours gardé
                '''if i == 1 and j == 1:
                    G.add_node((node_x, node_y))
                    continue

                trop_proche = False
                for bush_x, bush_y in bush_center:
                    if (node_x - bush_x)**2 + (node_y - bush_y)**2 < TILE_SIZE * TILE_SIZE:
                        trop_proche = True
                        break

                if not trop_proche:
                    G.add_node((node_x, node_y))'''
        '''for i in range(3):
            for j in range(3):
                node_x = round(x * TILE_SIZE + (2 * i + 1) * TILE_SIZE / 6, 4)
                node_y = round(y * TILE_SIZE + (2 * j + 1) * TILE_SIZE / 6, 4)

                trop_proche = False
                for bush_x, bush_y in bush_center:
                    if (node_x - bush_x)**2 + (node_y - bush_y)**2 < TILE_SIZE * TILE_SIZE:
                        trop_proche = True
                        break

                if not trop_proche:
                    G.add_node((node_x, node_y))'''
    # splitlines() découpe le texte ligne par ligne
    # sans garder les caractères \n
    lines = text.splitlines()


    # Il faut au minimum 4 lignes :
    # width
    # height
    # ---
    # ---
    # Même si height vaut 0 ce serait invalide, mais la structure minimale existe
    if len(lines) < 4:
        raise InvalidMapFileException("Fichier de map incomplet.")

    width_line = lines[0]
    height_line = lines[1]

    # Vérifie le format exact 'key: value'
    if not width_line.startswith("width: "):
        raise InvalidMapFileException("La ligne width est manquante ou mal formée.")

    if not height_line.startswith("height: "):
        raise InvalidMapFileException("La ligne height est manquante ou mal formée.")

    # Conversion des dimensions
    try:
        width = int(width_line.removeprefix("width: "))
        height = int(height_line.removeprefix("height: "))
    except ValueError:
        raise InvalidMapFileException("width et height doivent être des entiers.")

    # Les dimensions doivent être strictement positives
    if width <= 0 or height <= 0:
        raise InvalidMapFileException("width et height doivent être strictement positifs.")

    # Vérifie le premier séparateur ---
    if lines[2] != "---":
        raise InvalidMapFileException("Le séparateur --- avant la carte est manquant.")

    # Vérifie qu'il y a assez de lignes pour la carte + le séparateur final
    if len(lines) < 3 + height + 1:
        raise InvalidMapFileException("Le nombre de lignes de carte est insuffisant.")

    # Vérifie le séparateur final ---
    if lines[3 + height] != "---":
        raise InvalidMapFileException("Le séparateur --- après la carte est manquant.")

    grid = []
    player_positions = []
    bush_center = []
    cases_marchables = []

    # Lecture des height lignes de carte
    # Attention :
    # - la première ligne du fichier correspond à y = height - 1
    # - la dernière ligne du fichier correspond à y = 0
    for y_in_file in range(height):

        line = lines[3 + y_in_file]
        # Une ligne ne peut pas dépasser width caractères
        if len(line) > width:
            raise InvalidMapFileException("Une ligne de la carte dépasse la largeur indiquée.")

        row = []
        y_map = height - 1 - y_in_file

        for x in range(width):
            # Si la ligne est trop courte, les caractères manquants sont des espaces
            if x < len(line):
                char = line[x]
            else:
                char = " "

            if char == " ":
                row.append(GridCell.GRASS)
                cases_marchables.append((x, y_map))
            elif char == "x":
                row.append(GridCell.BUSH)
                bush_center.append(((x * TILE_SIZE) + TILE_SIZE/2, (y_map * TILE_SIZE) + TILE_SIZE/2))
            elif char == "*":
                row.append(GridCell.CRYSTAL)
                cases_marchables.append((x, y_map))
            elif char == "o":
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

            else:
                raise InvalidMapFileException(f"Caractère invalide dans la carte : {char!r}")

        # On insère au début pour que grid[0] corresponde à y = 0
        grid.insert(0, row)

    for x, y_map in cases_marchables:
        add_nodes_for_cell(x, y_map)
    s = Fraction(TILE_SIZE, 3)  # step exact en fraction pour éviter les erreurs float
    step = float(s)
    step_diag = step * sqrt(2)
    node_set = set(G.nodes)
    all_nodes = list(G.nodes)
    '''#limit_denominator n'est nécessaire que dans le sens float → Fraction, parce que le float est déjà imprécis :
# Dans la boucle des arêtes : float → Fraction (besoin de limit_denominator)
Fraction(node[0]).limit_denominator(TILE_SIZE)
# node[0] = 10.666666666666666  ← float approximatif, il faut deviner que c'est 32/3'''
    for node in all_nodes:
        fx = Fraction(node[0]).limit_denominator(TILE_SIZE)
        fy = Fraction(node[1]).limit_denominator(TILE_SIZE)

        voisins_droits = [
            (float(fx + s), float(fy)),
            (float(fx - s), float(fy)),
            (float(fx),     float(fy + s)),
            (float(fx),     float(fy - s)),
        ]
        for v in voisins_droits:
            if v in node_set:
                G.add_edge(node, v, weight=step)

        voisins_diagonaux = [
            (float(fx + s), float(fy + s)),
            (float(fx - s), float(fy + s)),
            (float(fx + s), float(fy - s)),
            (float(fx - s), float(fy - s)),
        ]
        for v in voisins_diagonaux:
            if v in node_set:
                G.add_edge(node, v, weight=step_diag)
    '''for node in all_nodes:
        x, y = node

        voisins_droits = [
        (round(x + step, 3), y),
        (round(x - step, 3), y),
        (x, round(y + step, 3)),
        (x, round(y - step, 3))
        ]
        for v in voisins_droits:
            if v in node_set:
                G.add_edge(node, v, weight=step)

        voisins_diagonaux = [
        (round(x + step, 3), round(y + step, 3)),
        (round(x - step, 3), round(y + step, 3)),
        (round(x + step, 3), round(y - step, 3)),
        (round(x - step, 3), round(y - step, 3))
        ]
        for v in voisins_diagonaux:
            if v in node_set:
                G.add_edge(node, v, weight=step_diag)'''

    '''all_nodes = list(G.nodes)
    for node in all_nodes:
        x, y = node

        # Voisins Droits (Poids TILE_SIZE)
        voisins_droits = [(x + TILE_SIZE, y), (x - TILE_SIZE, y), (x, y + TILE_SIZE), (x, y - TILE_SIZE)]
        for v in voisins_droits:
            if v in G.nodes:
                G.add_edge(node, v, weight=TILE_SIZE)

        # Voisins Diagonaux (Poids TILE_SIZE * sqrt(2))
        voisins_diagonaux = [
            (x + TILE_SIZE, y + TILE_SIZE), (x - TILE_SIZE, y + TILE_SIZE),
            (x + TILE_SIZE, y - TILE_SIZE), (x - TILE_SIZE, y - TILE_SIZE)
        ]
        for v in voisins_diagonaux:
            if v in G.nodes:
                G.add_edge(node, v, weight=TILE_SIZE * sqrt(2))'''
    # =========================================================
    # ÉTAPE 1 : Générer tous les noeuds valides
    # =========================================================


    '''seuil_carre = TILE_SIZE * TILE_SIZE
    distance = round(TILE_SIZE / 3, 2)
    distance_diag = round(distance * sqrt(2), 2)
    bush_center_set = set(bush_center)
    noeuds: set[tuple[float, float]] = set()

    for y in range(height):
        for x in range(width):

            cell = grid[y][x]
            if cell != GridCell.BUSH and cell != GridCell.HOLE:

                for i in range(1):
                    for j in range(1):

                        node_x = round(x * TILE_SIZE + (2 * i + 1) * TILE_SIZE / 6, 2)
                        node_y = round(y * TILE_SIZE + (2 * j + 1) * TILE_SIZE / 6, 2)

                        trop_proche = False

                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                bx = (x + dx) * TILE_SIZE + TILE_SIZE / 2
                                by = (y + dy) * TILE_SIZE + TILE_SIZE / 2
                                if (bx, by) in bush_center_set:
                                    if (node_x - bx)**2 + (node_y - by)**2 < seuil_carre:
                                        trop_proche = True
                                        break
                            if trop_proche:
                                break

                        if not trop_proche:
                            noeuds.add((node_x, node_y))

    # =========================================================
    # ÉTAPE 2 : Ajouter les noeuds au graphe
    # =========================================================

    G: nx.Graph[tuple[float, float]] = nx.Graph()
    G.add_nodes_from(noeuds)

    # =========================================================
    # ÉTAPE 3 : Connecter les noeuds voisins
    # =========================================================

    for noeud in noeuds:
        node_x = noeud[0]
        node_y = noeud[1]

        v1 = (round(node_x + distance, 2), node_y)
        v2 = (round(node_x - distance, 2), node_y)
        v3 = (node_x, round(node_y + distance, 2))
        v4 = (node_x, round(node_y - distance, 2))

        if v1 in noeuds:
            G.add_edge(noeud, v1, weight=distance)
        if v2 in noeuds:
            G.add_edge(noeud, v2, weight=distance)
        if v3 in noeuds:
            G.add_edge(noeud, v3, weight=distance)
        if v4 in noeuds:
            G.add_edge(noeud, v4, weight=distance)

        d1 = (round(node_x + distance, 2), round(node_y + distance, 2))
        d2 = (round(node_x - distance, 2), round(node_y + distance, 2))
        d3 = (round(node_x + distance, 2), round(node_y - distance, 2))
        d4 = (round(node_x - distance, 2), round(node_y - distance, 2))

        if d1 in noeuds:
            G.add_edge(noeud, d1, weight=distance_diag)
        if d2 in noeuds:
            G.add_edge(noeud, d2, weight=distance_diag)
        if d3 in noeuds:
            G.add_edge(noeud, d3, weight=distance_diag)
        if d4 in noeuds:
            G.add_edge(noeud, d4, weight=distance_diag)
    # =========================================================
    # ÉTAPE 4 : Vérification et retour
    # =========================================================





    for node in noeuds:
        x, y = node
        # On teste les 4 directions (Haut, Bas, Gauche, Droite)
        voisins_droit = [
            (round(x + distance, 1), y), (round(x - distance, 1), y),
            (x, round(y + distance, 1)), (x, round(y - distance, 1))
        ]

        for v in voisins_droit:
            if v in G.nodes: # Si le voisin est aussi un centre de case marchable
                G.add_edge(node, v, weight=distance)

        voisins_diagonaux = [
           (round(x + distance, 1), round(y + distance, 1)),
        (round(x - distance, 1), round(y + distance, 1)),
        (round(x + distance, 1), round(y - distance, 1)),
        (round(x - distance, 1), round(y - distance, 1)) #round ( ,1)= arrondie à l'entier
        ]

        for v in voisins_diagonaux:
            if v in G.nodes:
                # OPTIONNEL : Vérifier si le passage n'est pas "bloqué" par deux buissons en coin
                    # Pour éviter que le blob coupe à travers un coin de mur
                G.add_edge(node, v, weight=distance_diag)'''

    # Il faut exactement un seul P
    if len(player_positions) != 1:
        raise InvalidMapFileException("La carte doit contenir exactement un P.")

    player_start_x, player_start_y = player_positions[0]

    return Map(
        width=width,
        height=height,
        player_start_x=player_start_x,
        player_start_y=player_start_y,
        _grid=grid,
        navmesh=G,
    )


# Charge une map depuis un fichier texte
def load_map_from_file(filename: str) -> Map:
    try:
        with open(filename, "r", encoding="utf-8", newline="\n") as f:
            text = f.read()
    except OSError:
        raise InvalidMapFileException("Impossible de lire le fichier de map.")

    return load_map_from_string(text)


# Retourne la liste de tous les spinners présents sur la map
def find_spinners(game_map: Map) -> list[SpinnerData]:
    result = []

    for y in range(game_map.height):
        for x in range(game_map.width):
            cell = game_map.get(x, y)

            if cell == GridCell.SPINNER_HORIZONTAL:
                result.append(SpinnerData(x=x, y=y, is_horizontal=True))

            elif cell == GridCell.SPINNER_VERTICAL:
                result.append(SpinnerData(x=x, y=y, is_horizontal=False))

    return result
