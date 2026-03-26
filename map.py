# Travail de Nicolas SEMAINE 3
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


@dataclass(frozen=True) # on rend map immuable on empêche de modifier les attributs
class Map:
    width: int
    height: int
    player_start_x: int
    player_start_y: int
    _grid: list[list[GridCell]]# grille privée contenant les cellules de la map

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

_grille = []

for y in range(20):
    ligne = []
    for x in range(40):
        if (x == 0) or (x == 39) or (y == 0) or (y == 19):
            ligne.append(GridCell.BUSH)
        else:
            ligne.append(GridCell.GRASS)
    _grille.append(ligne)

_grille[6][3] = GridCell.BUSH
_grille[2][7] = GridCell.BUSH
_grille[10][2] = GridCell.BUSH
_grille[8][3] = GridCell.BUSH

_grille[2][5] = GridCell.CRYSTAL
_grille[5][6] = GridCell.CRYSTAL
_grille[5][3] = GridCell.CRYSTAL

MAP_DECOUVERTE = Map(
    width=40,
    height=20,
    player_start_x=2,
    player_start_y=2,
    _grid=_grille,
)

# Charge une map depuis une string Python
# Très utile pour les tests
def load_map_from_string(text: str) -> Map:
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

        for x in range(width):
            # Si la ligne est trop courte, les caractères manquants sont des espaces
            if x < len(line):
                char = line[x]
            else:
                char = " "

            if char == " ":
                row.append(GridCell.GRASS)

            elif char == "x":
                row.append(GridCell.BUSH)

            elif char == "*":
                row.append(GridCell.CRYSTAL)

            elif char == "o":
                row.append(GridCell.HOLE)

            elif char == "s":
                row.append(GridCell.SPINNER_HORIZONTAL)

            elif char == "S":
                row.append(GridCell.SPINNER_VERTICAL)

            elif char == "P":
                # P indique le point de départ du joueur
                # La cellule elle-même reste de l'herbe
                player_x = x
                player_y = height - 1 - y_in_file
                player_positions.append((player_x, player_y))
                row.append(GridCell.GRASS)
            elif char =="v":
                row.append(GridCell.BAT)

            else:
                raise InvalidMapFileException(f"Caractère invalide dans la carte : {char!r}")

        # On insère au début pour que grid[0] corresponde à y = 0
        grid.insert(0, row)

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


# Calcule les limites horizontales d'un spinner horizontal
# Retourne (left_x, right_x) inclus
# Le spinner peut se déplacer entre ces deux colonnes
def compute_horizontal_spinner_limits(game_map: Map, start_x: int, start_y: int) -> tuple[int, int]:
    # Vérifie que la case de départ contient bien un spinner horizontal
    if game_map.get(start_x, start_y) != GridCell.SPINNER_HORIZONTAL:
        raise ValueError("La position donnée ne contient pas un spinner horizontal.")

    # On cherche vers la gauche jusqu'au premier buisson
    left_x = start_x
    x = start_x - 1

    while x >= 0 and game_map.get(x, start_y) != GridCell.BUSH:
        left_x = x
        x -= 1

    # On cherche vers la droite jusqu'au premier buisson
    right_x = start_x
    x = start_x + 1

    while x < game_map.width and game_map.get(x, start_y) != GridCell.BUSH:
        right_x = x
        x += 1

    return (left_x, right_x)


# Calcule les limites verticales d'un spinner vertical
# Retourne (bottom_y, top_y) inclus
def compute_vertical_spinner_limits(game_map: Map, start_x: int, start_y: int) -> tuple[int, int]:
    # Vérifie que la case de départ contient bien un spinner vertical
    if game_map.get(start_x, start_y) != GridCell.SPINNER_VERTICAL:
        raise ValueError("La position donnée ne contient pas un spinner vertical.")

    # On cherche vers le bas jusqu'au premier buisson
    bottom_y = start_y
    y = start_y - 1

    while y >= 0 and game_map.get(start_x, y) != GridCell.BUSH:
        bottom_y = y
        y -= 1

    # On cherche vers le haut jusqu'au premier buisson
    top_y = start_y
    y = start_y + 1

    while y < game_map.height and game_map.get(start_x, y) != GridCell.BUSH:
        top_y = y
        y += 1

    return (bottom_y, top_y)
