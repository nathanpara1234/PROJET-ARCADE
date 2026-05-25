import arcade
from typing import Final
from enum import Enum
from constants import TILE_SIZE, SCALE
from textures import (
    TEXTURE_SWITCH_ON,
    TEXTURE_SWITCH_OFF,
    TEXTURE_GATE_CLOSED,
    TEXTURE_GATE_OPEN,
)
from gate_conditions import GateCondition
from map import SwitchData, GateData


def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


def make_tile_sprite(texture: arcade.Texture, x: int, y: int) -> arcade.Sprite:
    return arcade.Sprite(
        texture,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )


def make_tile_animation_sprite(
    animation: arcade.TextureAnimation,
    x: int,
    y: int,
) -> arcade.TextureAnimationSprite:
    return arcade.TextureAnimationSprite(
        animation=animation,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )


class SwitchSprite(arcade.Sprite):
    # Sprite visible de l'interrupteur.
    # Il garde aussi son id pour que les portails puissent le retrouver.
    id: str
    is_on: bool

    def __init__(self, switch: SwitchData) -> None:
        # On choisit la texture selon l'etat de depart lu dans la map.
        texture = TEXTURE_SWITCH_ON if switch.is_on else TEXTURE_SWITCH_OFF
        super().__init__(texture,scale=0.25,center_x=grid_to_pixels(switch.x),center_y=grid_to_pixels(switch.y),)
        self.id = switch.id
        self.is_on = switch.is_on

    def inverse_state_switch(self) -> None:
        self.is_on = not self.is_on
        if self.is_on:
            self.texture = TEXTURE_SWITCH_ON
        else:
            self.texture = TEXTURE_SWITCH_OFF


class GateSprite(arcade.Sprite):
    # open_if est la condition qui dit quand ce portail est ouvert.
    open_if: GateCondition
    is_open: bool

    def __init__(self, gate: GateData) -> None:
        super().__init__(TEXTURE_GATE_CLOSED,scale=SCALE,center_x=grid_to_pixels(gate.x),center_y=grid_to_pixels(gate.y),)
        self.open_if = gate.open_if
        self.is_open = False

    def set_open(self, is_open: bool) -> None:
        self.is_open = is_open
        if self.is_open:
            self.texture = TEXTURE_GATE_OPEN
        else:
            self.texture = TEXTURE_GATE_CLOSED


class WeaponType(Enum):
    BOOMERANG = 1
    SWORD = 2
