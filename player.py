from enum import Enum
import arcade  # ty:ignore[unresolved-import]

from constants import *
from textures import *


# Enum pour représenter clairement les 4 directions possibles du joueur.
# C'est mieux que des int ou des strings "libres", car :
# - c'est plus lisible
# - ça évite les valeurs invalides
# - le code est plus facile à maintenir
class Direction(Enum):
    NORTH = 1
    SOUTH = 2
    EAST = 3
    WEST = 4


class Player(arcade.TextureAnimationSprite):
    # direction : direction actuelle du joueur
    # up/down/left/right_pressed : état des touches
    # score : nombre de cristaux ramassés
    direction: Direction
    up_pressed: bool
    down_pressed: bool
    up_pressed : bool
    left_pressed: bool
    right_pressed: bool
    score: int

    def __init__(self, start_x: int, start_y: int) -> None:
        # On initialise le sprite animé avec l'animation idle vers le bas
        super().__init__(
            animation=ANIMATION_PLAYER_IDLE_DOWN,
            scale=SCALE,
            center_x=start_x,
            center_y=start_y,
        )

        # Au début du jeu, le joueur regarde vers le sud
        self.direction = Direction.SOUTH

        # Au départ, aucune touche n'est appuyée
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False

        # Score initial
        self.score = 0

    def player_move(self) -> None:
        # --- 1. Calcul du déplacement horizontal ---
        # On remet change_x à 0 avant de recalculer
        self.change_x = 0

        # Si seule la touche droite est appuyée, on va à droite
        if self.right_pressed and not self.left_pressed:
            self.change_x = PLAYER_MOVEMENT_SPEED

        # Si seule la touche gauche est appuyée, on va à gauche
        elif self.left_pressed and not self.right_pressed:
            self.change_x = -PLAYER_MOVEMENT_SPEED

        # --- 2. Calcul du déplacement vertical ---
        # Même idée pour l'axe vertical
        self.change_y = 0

        if self.up_pressed and not self.down_pressed:
            self.change_y = PLAYER_MOVEMENT_SPEED

        elif self.down_pressed and not self.up_pressed:
            self.change_y = -PLAYER_MOVEMENT_SPEED

        # --- 3. Mise à jour de la direction regardée ---
        # On respecte l'ordre demandé par la consigne :
        # bas > haut > gauche > droite
        #
        # Donc si plusieurs touches sont enfoncées en même temps,
        # cet ordre décide de la direction affichée.
        if self.down_pressed:
            self.direction = Direction.SOUTH
        elif self.up_pressed:
            self.direction = Direction.NORTH
        elif self.left_pressed:
            self.direction = Direction.WEST
        elif self.right_pressed:
            self.direction = Direction.EAST
        # sinon : aucune touche n'est appuyée
        # => on garde la direction précédente

        # --- 4. Choix de l'animation selon la direction ---
        # Ici on affiche l'animation idle correspondant à la direction
        if self.direction == Direction.NORTH:
            self.animation = ANIMATION_PLAYER_IDLE_UP
        elif self.direction == Direction.SOUTH:
            self.animation = ANIMATION_PLAYER_IDLE_DOWN
        elif self.direction == Direction.EAST:
            self.animation = ANIMATION_PLAYER_IDLE_RIGHT
        elif self.direction == Direction.WEST:
            self.animation = ANIMATION_PLAYER_IDLE_LEFT
