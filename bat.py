from math import cos, sin
import random
import arcade
from textures import *
from constants import *
import math


class Bat(arcade.TextureAnimationSprite):
    direction: float
    start_x: int
    start_y: int

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
            self.start_x - 30 < x < self.start_x + 300
            and self.start_y - 300 < y < self.start_y + 300
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
