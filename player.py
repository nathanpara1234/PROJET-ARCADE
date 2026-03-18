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
    down_pressed: bool
    up_pressed : bool
    left_pressed: bool
    right_pressed: bool
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

    def is_moving (self) ->bool:
        return self.change_x != 0 or self.change_y != 0


    def animation_orientation (self) -> None:

        if self.direction == Direction.South:
            if self.is_moving():
                self.animation = ANIMATION_PLAYER_RUN_DOWN
            else:
                self.animation = ANIMATION_PLAYER_IDLE_DOWN

        elif self.direction == Direction.North:
            if self.is_moving():
                self.animation = ANIMATION_PLAYER_RUN_UP
            else:
                self.animation = ANIMATION_PLAYER_IDLE_UP

        elif self.direction == Direction.West:
            if self.is_moving():
                self.animation = ANIMATION_PLAYER_RUN_LEFT
            else:
                self.animation = ANIMATION_PLAYER_IDLE_LEFT

        elif self.direction == Direction.East:
            if self.is_moving():
                self.animation = ANIMATION_PLAYER_RUN_RIGHT
            else:
                self.animation = ANIMATION_PLAYER_IDLE_RIGHT
