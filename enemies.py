from math import cos, sin
import random
import arcade
from textures import *
from constants import *
import math
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
