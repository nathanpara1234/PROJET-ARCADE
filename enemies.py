import networkx as nx
from math import cos, sin, sqrt
import random
import arcade
from abc import abstractmethod
from textures import *
from constants import *
import math
from player import *
from map import (
    Map,
    GridCell,
    SpinnerData
)

class SpinnerSprite(arcade.TextureAnimationSprite):
    is_horizontal: bool
    min_pos: int
    max_pos: int

    def spinner_move(self) -> None:
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.is_horizontal:
                # Le spinner inverse sa direction s’il atteint une borne
            if self.center_x >= self.max_pos:
                self.center_x = self.max_pos
                self.change_x = -SPINNER_SPEED
            elif self.center_x <= self.min_pos:
                self.center_x = self.min_pos
                self.change_x = SPINNER_SPEED
        else:
            if self.center_y >= self.max_pos:
                self.center_y = self.max_pos
                self.change_y = -SPINNER_SPEED
            elif self.center_y <= self.min_pos:
                self.center_y = self.min_pos
                self.change_y = SPINNER_SPEED

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

#fct qui regroupe les deux précédentes mais qui est plus complexe
def compute_spinner_limits(game_map: Map, start_x: int, start_y: int, is_horizontal: bool) -> tuple[int, int]:
    if is_horizontal:
        if game_map.get(start_x, start_y) != GridCell.SPINNER_HORIZONTAL:
            raise ValueError("La position donnée ne contient pas un spinner horizontal.")
    else:
        if game_map.get(start_x, start_y) != GridCell.SPINNER_VERTICAL:
            raise ValueError("La position donnée ne contient pas un spinner vertical.")

    # On cherche vers la gauche (horizontal) ou vers le bas (vertical)
    min_pos = start_x if is_horizontal else start_y
    i = min_pos - 1

    while i >= 0:
        x, y = (i, start_y) if is_horizontal else (start_x, i)
        if game_map.get(x, y) == GridCell.BUSH:
            break
        min_pos = i
        i -= 1

    # On cherche vers la droite (horizontal) ou vers le haut (vertical)
    max_pos = start_x if is_horizontal else start_y
    i = max_pos + 1
    limit = game_map.width if is_horizontal else game_map.height

    while i < limit:
        x, y = (i, start_y) if is_horizontal else (start_x, i)
        if game_map.get(x, y) == GridCell.BUSH:
            break
        max_pos = i
        i += 1

    return (min_pos, max_pos)




class Enemy(arcade.TextureAnimationSprite):
    @abstractmethod
    def move(self, navmesh: nx.Graph, player_pos: tuple[float, float] | None) -> None:
        ...


class Bat(Enemy):
    direction: float
    start_x: int
    start_y: int
    path: list
    i : int
    world_width: int
    world_height: int

    def __init__(self, start_x: int, start_y: int, world_width: int, world_height: int) -> None:
        super().__init__(
            animation=ANIMATION_BAT,
            scale=SCALE,
            center_x=start_x,
            center_y=start_y,
        )
        self.direction = random.uniform(0, 360)
        self.start_x = start_x
        self.start_y = start_y
        self.world_width = world_width
        self.world_height = world_height

    def valid_pos(self, x: float, y: float) -> bool:
        min_x = max(TILE_SIZE, self.start_x - 100)
        max_x = min(self.world_width - TILE_SIZE, self.start_x + 100)
        min_y = max(TILE_SIZE, self.start_y - 100)
        max_y = min(self.world_height - TILE_SIZE, self.start_y + 100)
        return min_x < x < max_x and min_y < y < max_y

    def move(self, navmesh: nx.Graph, player_pos: tuple[float, float] | None) -> None:

        condition_move = random.uniform(0, 100)
        #on choisit un nombre aléatoirement entre 0 et 100
        # et on fais changer la bat de direction que si le nombre est inférieur à 2
        # ce qui fait que la bat change de direction à 2% des frames
        if condition_move < 2:
            self.direction = random.uniform(self.direction - 30, self.direction + 30)

        #on fait avancé la bat que si la prochaine frame la bat est encore à l'intérieur de la zone
        next_x = self.center_x + BAT_MOUVEMENT_SPEED * cos((self.direction * math.pi) / 180)
        next_y = self.center_y + BAT_MOUVEMENT_SPEED * sin((self.direction * math.pi) / 180)

        if self.valid_pos(next_x, next_y):
            self.center_x = next_x
            self.center_y = next_y
        # si la bat est hors de la zone à la frame suivante, elle fait demi tour
        else:
            self.direction = (self.direction + 180) % 360

class Blob(Enemy):
    target_x: float
    target_y: float
    start_x: float
    start_y: float


    def __init__(self, start_x: int, start_y: int) -> None:
        super().__init__(
            animation=ANIMATION_BLOB,
            scale=SCALE,
            center_x=start_x,
            center_y=start_y,
        )
        self.target_x = start_x
        self.target_y = start_y
        self.start_x = start_x
        self.start_y = start_y
        self.path = []
        self.i = 0
    def valid_pos(self, x: float, y: float) -> bool:
        #fonction qui définit la zone de patrouille du blob
        return (
            self.start_x - 4*TILE_SIZE < x < self.start_x + 4*TILE_SIZE
            and self.start_y - 4*TILE_SIZE < y < self.start_y + 4*TILE_SIZE
        )


    def new_target (self, G : nx.Graph, target_player:  tuple[float, float] | None) -> None:
        path_found = False
        limit = 4 * TILE_SIZE
        all_nodes = list(G.nodes)


        pos_blob = min(all_nodes, key=lambda n: (n[0] - self.center_x)**2 + (n[1] - self.center_y)**2)
        #donne le noeud le plus proche du blob afin de creer le chemin
        composante = nx.node_connected_component(G, pos_blob)

        while not path_found:
            if target_player is not None:
                #prend les coordonées du player si il est dans la zone de vision du blob
                self.target_x = target_player[0]
                self.target_y = target_player[1]
            else:
                raw_min_x = self.start_x - limit
                raw_max_x = self.start_x + limit
                raw_min_y = self.start_y - limit
                raw_max_y = self.start_y + limit

                zone_min_x = max(0, raw_min_x)
                zone_max_x = min(MAX_WINDOW_WIDTH, raw_max_x)
                zone_min_y = max(0, raw_min_y)
                zone_max_y = min(MAX_WINDOW_HEIGHT, raw_max_y)
                #les lignes précédentes calculs une zone dans laquelle on va choisir au hasard un point dans la map
                self.target_x = random.randrange(int(min(zone_min_x, zone_max_x)), int(max(zone_min_x, zone_max_x) + 1), TILE_SIZE // 2)
                self.target_y = random.randrange(int(min(zone_min_y, zone_max_y)), int(max(zone_min_y, zone_max_y) + 1), TILE_SIZE // 2)

            # donne le noeud le plus proche de la cible
            pos_target = min(all_nodes, key=lambda n: (n[0] - self.target_x)**2 + (n[1] - self.target_y)**2)

            if pos_target in composante:
                try:
                    #creer le chemin avec dikstra, en tenant compte de la longeur des arrêtes
                    self.path = nx.dijkstra_path(G, pos_blob, pos_target, weight='weight')
                    self.i = 0
                    if self.path:
                        path_found = True
                except Exception as e:
                    print(f"erreur : {e}")
            else:
                if target_player is not None:
                    break

    def move(self, navmesh: nx.Graph, player_pos: tuple[float, float] | None) -> None:
        #Sécurité : si on n'a pas de chemin
        if self.i >= len(self.path):
            self.new_target(navmesh, None)
            return

        intermediaire_target_x = self.path[self.i][0]
        intermediaire_target_y = self.path[self.i][1]

        distance_x =  intermediaire_target_x - self.center_x
        distance_y = intermediaire_target_y - self.center_y
        distance_minimale = (sqrt(distance_x**2 + distance_y**2))

        if distance_minimale < 2:  # On est arrivé au point intermédiaire
            if player_pos is not None:
                # si le jouuer est dans la zone, on calcule une nouvelle position
                self.new_target(navmesh, player_pos)
                # On met self.i = 1 dans new_target pour ne pas revenir sur ce noeud
                self.i = 1
            else:

                if self.i >= len(self.path) - 1:
                    # Arrivé au bout de la patrouille, on en cherche une nouvelle cible aléatoire
                    self.new_target(navmesh, None)
                else:
                    # On passe simplement au point suivant
                    self.i += 1
            return # On s'arrête là pour cette frame pour éviter de bouger deux fois

        #MOUVEMENT (seulement si on n'est pas sur un noeud)
        cos_move = distance_x / distance_minimale
        sin_move = distance_y / distance_minimale
        self.center_x += 1 * cos_move
        self.center_y += 1 * sin_move
