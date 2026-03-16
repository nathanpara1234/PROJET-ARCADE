from enum import Enum
from typing import Final
import arcade

from constants import *
from textures import *

class Direction(Enum):
    North = 1
    South = 2
    East = 3
    West = 4

class Player(arcade.TextureAnimationSprite):
    direction : Direction
    up_pressed : bool
    down_pressed: bool
    right_pressed: bool
    left_pressed: bool
    score: int

    def __init__(self,start_x: int, start_y: int) -> None:
        super().__init__(
            animation = ANIMATION_PLAYER_IDLE_DOWN,
            scale = SCALE,
            center_x = start_x,
            center_y= start_y,
        )
        self.direction = Direction.South #initialisation sud
        self.up_pressed = False     #initialisation
        self.down_pressed = False
        self.left_pressed = False
        self.right_pressed = False
        self.score = 0

    def player_move (self) -> None:
        self.change_x = 0      #horizontal
        if self.right_pressed and not self.left_pressed:
            self.change_x = PLAYER_MOVEMENT_SPEED
            self.direction = Direction.East
        elif self.left_pressed and not self.right_pressed:
            self.change_x = -PLAYER_MOVEMENT_SPEED
            self.direction = Direction.West


        self.change_y = 0   #vertical
        if self.up_pressed and not self.down_pressed:
            self.change_y = PLAYER_MOVEMENT_SPEED
            self.direction = Direction.North
        elif self.down_pressed and not self.up_pressed:
            self.change_y = -PLAYER_MOVEMENT_SPEED
            self.direction = Direction.South
