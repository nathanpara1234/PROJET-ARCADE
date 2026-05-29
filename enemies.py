import networkx as nx
from math import cos, sin, sqrt
import random
import arcade
from abc import abstractmethod
from typing import Final
from textures import ANIMATION_BAT, ANIMATION_BLOB, ANIMATION_SPINNER
from constants import SPINNER_SPEED, SCALE, TILE_SIZE, BAT_MOUVEMENT_SPEED, MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT, BAT_FRAQUENCY_MODIF_DIRECTION, BLOB_MOUVEMENT_SPEED, BAT_ZONE_WIDTH, BLOB_ZONE_WIDTH
import math
from player import Player

class SpinnerSprite(arcade.TextureAnimationSprite):
    """Ennemi qui fait des allers-retours entre deux bornes fixes sur un axe."""

    is_horizontal: Final[bool]
    min_pos: Final[float]
    max_pos: Final[float]
    change_x: float
    change_y: float

    def __init__(self, center_x: float, center_y: float, is_horizontal: bool, min_pos: float, max_pos: float) -> None:
        super().__init__(
            animation=ANIMATION_SPINNER,
            scale=SCALE,
            center_x=center_x,
            center_y=center_y,
        )
        self.is_horizontal = is_horizontal
        self.min_pos = min_pos
        self.max_pos = max_pos
        self.change_x = SPINNER_SPEED if is_horizontal else 0
        self.change_y = 0 if is_horizontal else SPINNER_SPEED

    def bounce(self, pos: float, speed: float) -> tuple[float, float]:
        # demi tour si le spinner atteint une limite, sinon il continu
        if pos >= self.max_pos:
            return (self.max_pos, -SPINNER_SPEED)
        elif pos <= self.min_pos:
            return (self.min_pos, SPINNER_SPEED)
        return (pos, speed)

    def spinner_move(self) -> None:
        # deplace le spinner puis verifie s'il doit faire demi tour
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.is_horizontal:
            (self.center_x, self.change_x) = self.bounce(self.center_x, self.change_x)
        else:
            (self.center_y, self.change_y) = self.bounce(self.center_y, self.change_y)


class Enemy(arcade.TextureAnimationSprite):
    """Classe de base pour les ennemis intelligents (Bat, Blob),
    SpinnerSprite n'en hérite pas car son déplacement est constant"""

    # position de départ et taille du monde, communs à tous les ennemis
    start_x: Final[int]
    start_y: Final[int]
    world_width: Final[int]
    world_height: Final[int]

    def __init__(self, animation: arcade.TextureAnimation, start_x: int, start_y: int, world_width: int, world_height: int) -> None:
        super().__init__(
            animation=animation,
            scale=SCALE,
            center_x=start_x,
            center_y=start_y,
        )
        self.start_x = start_x
        self.start_y = start_y
        self.world_width = world_width
        self.world_height = world_height

    @abstractmethod
    def move(self, navmesh: nx.Graph, player_pos: tuple[float, float] | None) -> None:
        #Déplace l'ennemi d'une frame.
        ...


class Bat(Enemy):
    """Ennemi qui se déplace aléatoirement dans un rayon fixe autour de sa position de départ."""

    direction: float

    def __init__(self, start_x: int, start_y: int, world_width: int, world_height: int) -> None:
        super().__init__(ANIMATION_BAT, start_x, start_y, world_width, world_height)
        self.direction = random.uniform(0, 360)

    def valid_pos(self, x: float, y: float) -> bool:
        min_x = max(TILE_SIZE, self.start_x - BAT_ZONE_WIDTH)             # bord gauche : au moins TILE_SIZE du mur (pour pas qu'elle soit en dehors de la map)
        max_x = min(self.world_width - TILE_SIZE, self.start_x + BAT_ZONE_WIDTH)  # bord droit : au plus TILE_SIZE du mur
        min_y = max(TILE_SIZE, self.start_y - BAT_ZONE_WIDTH)
        max_y = min(self.world_height - TILE_SIZE, self.start_y + BAT_ZONE_WIDTH)
        return min_x < x < max_x and min_y < y < max_y


    def move(self, navmesh: nx.Graph, player_pos: tuple[float, float] | None) -> None:

        condition_move = random.uniform(0, 100)
        #on choisit un nombre aléatoirement entre 0 et 100
        # et on fais changer la bat de direction que si le nombre est inférieur à 2
        # ce qui fait que la bat change de direction à BAT_FRAQUENCY_MODIF_DIRECTION% des frames
        if condition_move < BAT_FRAQUENCY_MODIF_DIRECTION:
            self.direction = random.uniform(self.direction - 30, self.direction + 30)

        #on fait avancé la bat que si la prochaine frame la bat est encore à l'intérieur de la zone
        next_x = self.center_x + BAT_MOUVEMENT_SPEED * cos((self.direction * math.pi) / 180)
        next_y = self.center_y + BAT_MOUVEMENT_SPEED * sin((self.direction * math.pi) / 180)

        if self.valid_pos(next_x, next_y):
            self.center_x = next_x
            self.center_y = next_y
        # si la bat est hors de la zone à la frame suivante, elle fait demi tour
        else:
            self.direction = (self.direction + random.uniform(135, 225)) % 360# definit langle de deviation du bat

class Blob(Enemy):
    """Ennemi qui suit le joueur via Dijkstra sur le navmesh quand il le voit, sinon erre aléatoirement."""

    target_x: float
    target_y: float
    path : list
    i : int

    def __init__(self, start_x: int, start_y: int, world_width: int, world_height: int) -> None:
        super().__init__(ANIMATION_BLOB, start_x, start_y, world_width, world_height)
        self.target_x = start_x
        self.target_y = start_y
        self.path = []
        self.i = 0
    @staticmethod
    # calcul le noeud du graphe le plus proche d'un point
    def closest_node (G : nx.Graph, x: float, y : float) -> tuple[float, float] :
        all_nodes = list(G.nodes)
        return min(all_nodes,  key=lambda n: (n[0] - x)**2 + (n[1] - y)**2)

    @staticmethod
    def random_axis(start: float, limit: float, world_max: float) -> int:
        zone_min = max(0, start - limit)          # bord gauche(x)/bas(y) de la zone, pour ne pas sortir de la map
        zone_max = min(world_max, start + limit)  # bord droit(x)/haut(y) de la zone
        return random.randrange(
            int(zone_min),     # valeur minimale possible
            int(zone_max + 1)  # valeur maximale possible (+1 car randrange est exclusif)
        )

    def new_target (self, G : nx.Graph, target_player:  tuple[float, float] | None) -> None:
        path_found = False
        limit = BLOB_ZONE_WIDTH
        all_nodes = list(G.nodes)

        #donne le noeud le plus proche du blob afin de creer le chemin
        pos_blob = self.closest_node (G, self.center_x, self.center_y)
        composante = nx.node_connected_component(G, pos_blob)

        while not path_found:
            if target_player is not None:
                #prend les coordonées du player si il est dans la zone de vision du blob
                self.target_x = target_player[0]
                self.target_y = target_player[1]
            else:
                self.target_x = self.random_axis(self.start_x, limit, self.world_width)   #coord x au hasard
                self.target_y = self.random_axis(self.start_y, limit, self.world_height)  #coord y au hasard

            # donne le noeud le plus proche de la cible
            pos_target = self.closest_node(G, self.target_x, self.target_y)

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
        # si on n'a pas de chemin
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
                # on met self.i = 1 dans new_target pour ne pas revenir sur ce noeud
                self.i = 1
            else:

                if self.i >= len(self.path) - 1:
                    # à la cible, on en cherche une nouvelle cible aléatoire
                    self.new_target(navmesh, None)
                else:
                    #  sinon on passe simplement au point suivant
                    self.i += 1
            return # on s'arrête là pour cette frame pour éviter de bouger deux fois

        # avance (seulement si on n'est pas sur un noeud)
        cos_move = distance_x / distance_minimale
        sin_move = distance_y / distance_minimale
        self.center_x += BLOB_MOUVEMENT_SPEED * cos_move
        self.center_y += BLOB_MOUVEMENT_SPEED * sin_move
