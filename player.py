from enum import Enum, auto
import arcade

from constants import *
from textures import *

class Direction(Enum):
    NORTH = auto()
    SOUTH = auto()
    EAST = auto()
    WEST = auto()


class Player(arcade.TextureAnimationSprite):
    """Sprite du joueur : gère le mouvement, la direction, le score et l'invincibilité temporaire."""

    direction: Direction
    up_pressed: bool
    down_pressed: bool
    left_pressed: bool
    right_pressed: bool
    score: int
    key : int
    __indestructible: bool
    __indestructibility_timer: int

    def __init__(self, start_x: int, start_y: int) -> None:
        # On initialise le sprite animé avec l'animation idle vers le bas
        super().__init__(
            animation=ANIMATION_PLAYER_IDLE_DOWN,
            scale=SCALE,
            center_x=start_x,
            center_y=start_y,
        )

        self.direction = Direction.SOUTH
        self.up_pressed = False
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.__indestructible = False
        self.__indestructibility_timer = 0
        self.score = 0
        self.key = 0

    @property
    def indestructible(self) -> bool:
        return self.__indestructible
    def player_move(self) -> None:
        self.change_x = 0
        if self.right_pressed and not self.left_pressed:
            self.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.change_x = -PLAYER_MOVEMENT_SPEED

        self.change_y = 0
        if self.up_pressed and not self.down_pressed:
            self.change_y = PLAYER_MOVEMENT_SPEED
        elif self.down_pressed and not self.up_pressed:
            self.change_y = -PLAYER_MOVEMENT_SPEED
        # On associe chaque touche à une direction
        if self.down_pressed:
            self.direction = Direction.SOUTH
        elif self.up_pressed:
            self.direction = Direction.NORTH
        elif self.left_pressed:
            self.direction = Direction.WEST
        elif self.right_pressed:
            self.direction = Direction.EAST

        SHIELD_TEXTURES = {
            Direction.NORTH: TEXTURE_SHIELDED_UP,
            Direction.SOUTH: TEXTURE_SHIELDED_DOWN,
            Direction.EAST:  TEXTURE_SHIELDED_RIGHT,
            Direction.WEST:  TEXTURE_SHIELDED_LEFT,
        }
        IDLE_ANIMATIONS = {
            Direction.NORTH: ANIMATION_PLAYER_IDLE_UP,
            Direction.SOUTH: ANIMATION_PLAYER_IDLE_DOWN,
            Direction.EAST:  ANIMATION_PLAYER_IDLE_RIGHT,
            Direction.WEST:  ANIMATION_PLAYER_IDLE_LEFT,
        }
        if self.indestructible:
            self.texture = SHIELD_TEXTURES[self.direction]
        else:
            self.animation = IDLE_ANIMATIONS[self.direction]

    def player_become_indestructible(self) -> None:
        self.__indestructible = True
        self.__indestructibility_timer = INDESTRUCTIBILITY_DURATION

    def update_invincibility(self) -> None:
        # si le joueur est invincible on réduit le timer, et quand il tombe à 0 on enlève l'invincibilité
        if not self.__indestructible:
            return
        self.__indestructibility_timer -= 1
        if self.__indestructibility_timer <= 0:
            self.__indestructible = False
            self.__indestructibility_timer = 0
