import networkx as nx
from math import cos, sin, sqrt
import random
import arcade
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
                self.change_x = -3
            elif self.center_x <= self.min_pos:
                self.center_x = self.min_pos
                self.change_x = 3
        else:
            if self.center_y >= self.max_pos:
                self.center_y = self.max_pos
                self.change_y = -3
            elif self.center_y <= self.min_pos:
                self.center_y = self.min_pos
                self.change_y = 3

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




class Bat(arcade.TextureAnimationSprite):
    direction: float
    start_x: int
    start_y: int
    path: list
    i : int

    def __init__(self, start_x: int, start_y: int) -> None:
        super().__init__(
            animation=ANIMATION_BAT,
            scale=SCALE,
            center_x=start_x,
            center_y=start_y,
        )
        self.direction = random.uniform(0, 360)
        self.start_x = start_x
        self.start_y = start_y

    def valid_pos(self, x: float, y: float) -> bool:
        return (
            self.start_x - 100 < x < self.start_x + 100
            and self.start_y - 100 < y < self.start_y + 100
            and 0 < x < 40*TILE_SIZE and 0 < y < 15*TILE_SIZE
        )

    def bat_move(self) -> None:
        condition_move = random.uniform(0, 100)

        if condition_move < 2:
            self.direction = random.uniform(self.direction - 30, self.direction + 30)

        next_x = self.center_x + 2 * cos((self.direction * math.pi) / 180)
        next_y = self.center_y + 2 * sin((self.direction * math.pi) / 180)

        if self.valid_pos(next_x, next_y):
            self.center_x = next_x
            self.center_y = next_y
        else:
            self.direction = (self.direction + 180) % 360

class Blob (arcade.TextureAnimationSprite):
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
        return (
            self.start_x - 4*TILE_SIZE < x < self.start_x + 4*TILE_SIZE
            and self.start_y - 4*TILE_SIZE < y < self.start_y + 4*TILE_SIZE
        )



    def new_target (self, G : nx.Graph, target_player:  tuple[float, float] | None) -> None:
        path_found = False
        limit = 4 * TILE_SIZE
        all_nodes = list(G.nodes)


        pos_blob = min(all_nodes, key=lambda n: (n[0] - self.center_x)**2 + (n[1] - self.center_y)**2)
    # Calculé UNE SEULE FOIS avant la boucle
        composante = nx.node_connected_component(G, pos_blob)

        while not path_found:
            if target_player is not None:
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

                self.target_x = random.randrange(int(min(zone_min_x, zone_max_x)), int(max(zone_min_x, zone_max_x) + 1), TILE_SIZE // 2)
                self.target_y = random.randrange(int(min(zone_min_y, zone_max_y)), int(max(zone_min_y, zone_max_y) + 1), TILE_SIZE // 2)

            pos_target = min(all_nodes, key=lambda n: (n[0] - self.target_x)**2 + (n[1] - self.target_y)**2)

            if pos_target in composante:
                try:
                    self.path = nx.dijkstra_path(G, pos_blob, pos_target, weight='weight')
                    self.i = 0
                    if self.path:
                        path_found = True
                        print("chemin trouvé !")
                except Exception as e:
                    print(f"erreur : {e}")
            else:
                if target_player is not None:
                    break

        '''path_found = False
        limit =  4* TILE_SIZE
        all_nodes = list(G.nodes)

         # 2. On s'assure que le blob est bien dans le graph, sinon on le replace
        pos_blob = min(all_nodes, key=lambda n: (n[0] - self.center_x)**2 + (n[1] - self.center_y)**2)
        #print(f"pos_blob : {pos_blob}")
        #print(f"pos_blob in G.nodes : {pos_blob in G.nodes}")

    # On boucle jusqu'à trouver un chemin qui marche
        while not path_found:
            if target_player is not None:
                # Si on a passé une position (le joueur), on l'utilise !
                self.target_x = target_player[0]
                self.target_y = target_player[1]
                path_found = True
            else :

                raw_min_x = self.start_x - limit
                raw_max_x = self.start_x + limit
                raw_min_y = self.start_y - limit
                raw_max_y = self.start_y + limit

            # 3. ON LIMITE À LA ZONE RÉELLE DE LA MAP (Clamping)
            # max(0, ...) empêche d'aller en négatif
            # min(max_x, ...) empêche de sortir à droite/en haut
                zone_min_x = max(0, raw_min_x)
                zone_max_x = min(MAX_WINDOW_WIDTH, raw_max_x)
                zone_min_y = max(0, raw_min_y)
                zone_max_y = min(MAX_WINDOW_HEIGHT, raw_max_y)

                self.target_x = random.randrange(int(min(zone_min_x, zone_max_x)), int(max(zone_min_x, zone_max_x) + 1), TILE_SIZE // 2)
                self.target_y = random.randrange(int(min(zone_min_y, zone_max_y)), int(max(zone_min_y, zone_max_y) + 1), TILE_SIZE // 2)


                pos_target = min(all_nodes, key=lambda n: (n[0]-self.target_x)**2 + (n[1]-self.target_y)**2)
                composante = nx.node_connected_component(G, pos_blob)
                if pos_target in composante:
                    try:
                        self.path = nx.astar_path(G, pos_blob, pos_target, weight='weight')
                        self.i = 0
                        if self.path:
                            path_found = True
                    except : #Exception as e:
                        #print(f"erreur : {e}")
                        pass
                else:
                    if target_player is not None:
                        break'''
               # print(f"pos_target : {pos_target}")
                #print(f"pos_target in G.nodes : {pos_target in G.nodes}")
        '''composante = nx.node_connected_component(G, pos_blob)
                #print(f"pos_target in composante : {pos_target in composante}")
                if pos_target in composante:
                    try:
                        self.path = nx.astar_path(G, pos_blob, pos_target, weight='weight')
                        self.i = 0
                        if self.path:
                            path_found = True
                            print("chemin trouvé !")
                    except Exception as e:
                        print(f"erreur : {e}")
                        path_found = False'''


        '''try:
                    rayon = 6 * TILE_SIZE * 6 * TILE_SIZE
                    noeuds_proches = [
                        n for n in G.nodes
                        if (n[0] - self.center_x)**2 + (n[1] - self.center_y)**2 <= rayon
                    ]
                    sous_graphe = G.subgraph(noeuds_proches)

                    if pos_blob in sous_graphe.nodes and pos_target in sous_graphe.nodes:
                        self.path = nx.astar_path(sous_graphe, pos_blob, pos_target, weight='weight')
                    else:
                        self.path = nx.astar_path(G, pos_blob, pos_target, weight='weight')

                    self.i = 0
                    if self.path:
                        path_found = True
                except Exception as e:
                    print(f"erreur : {e}")
    # Fallback sur le graphe complet
                    try:
                        self.path = nx.astar_path(G, pos_blob, pos_target, weight='weight')
                        self.i = 0
                        if self.path:
                            path_found = True
                    except:
                        pass'''

        '''try:
                rayon = 6 * TILE_SIZE * 6 * TILE_SIZE

                noeuds_proches = [
                    n for n in G.nodes
                    if (n[0] - self.center_x)**2 + (n[1] - self.center_y)**2 <= rayon
                ]

                sous_graphe = G.subgraph(noeuds_proches)

                if pos_blob in sous_graphe.nodes and pos_target in sous_graphe.nodes:
                    self.path = nx.astar_path(sous_graphe, pos_blob, pos_target, weight='weight')
                else:
                    self.path = nx.astar_path(G, pos_blob, pos_target, weight='weight')

                self.i = 0
                if self.path:
                    path_found = True
            except:
                pass'''

    def blob_move(self, G: nx.Graph, target_player : tuple[float, float] | None) -> None:
        # 1. Sécurité : si on n'a pas de chemin
        if self.i >= len(self.path):
            self.new_target(G, None)
            return



        intermediaire_target_x = self.path[self.i][0]
        intermediaire_target_y = self.path[self.i][1]

        distance_x =  intermediaire_target_x - self.center_x
        distance_y = intermediaire_target_y - self.center_y
        distance_minimale = (sqrt(distance_x**2 + distance_y**2))

        # 3. GESTION DE L'ARRIVÉE SUR UN NOEUD
        if distance_minimale < 2:  # On est arrivé au point intermédiaire
            if target_player is not None:
                # MODE CHASSE : On recalcule vers la position actuelle du joueur
                self.new_target(G, target_player)
                # On met self.i = 1 dans new_target pour ne pas revenir sur ce noeud
                self.i = 1
            else:
                # MODE PATROUILLE
                if self.i >= len(self.path) - 1:
                    # Arrivé au bout de la patrouille, on en cherche une nouvelle
                    self.new_target(G, None)
                else:
                    # On passe simplement au point suivant
                    self.i += 1
            return # On s'arrête là pour cette frame pour éviter de bouger deux fois

        # 4. MOUVEMENT (seulement si on n'est pas sur un noeud)
        cos_move = distance_x / distance_minimale
        sin_move = distance_y / distance_minimale
        self.center_x += 1 * cos_move
        self.center_y += 1 * sin_move
