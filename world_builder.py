from dataclasses import dataclass
from typing import Final
import arcade

from constants import TILE_SIZE, SCALE, SPINNER_SPEED
from enemies import Bat, Blob, SpinnerSprite
from map import GateData, GridCell, Map, SwitchData
from interactions import update_gate_states
from textures import (
    TEXTURE_GRASS,
    TEXTURE_BUSH,
    TEXTURE_HOLE,
    TEXTURE_GATE_CLOSED,
    TEXTURE_GATE_OPEN,
    TEXTURE_SWITCH_OFF,
    TEXTURE_SWITCH_ON,
    ANIMATION_CRYSTALS,
    ANIMATION_KEY,
    ANIMATION_CHEST,
    ANIMATION_SPIKES,
)


# convertit une coordonnee grille en pixels
def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


# crée un sprite statique à la position grille (x, y)
def make_tile_sprite(texture: arcade.Texture, x: int, y: int) -> arcade.Sprite:
    return arcade.Sprite(
        texture,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )


# crée un sprite animé a la position grille (x, y)
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


# sprite d'interrupteur : change de texture quand il est active ou desactive
class SwitchSprite(arcade.Sprite):
    id: Final[str]
    __is_on: bool

    def __init__(self, switch_data: SwitchData) -> None:
        texture = TEXTURE_SWITCH_ON if switch_data.is_on else TEXTURE_SWITCH_OFF
        super().__init__(
            texture,
            scale=0.25,
            center_x=grid_to_pixels(switch_data.x),
            center_y=grid_to_pixels(switch_data.y),
        )
        self.id = switch_data.id
        self.__is_on = switch_data.is_on

    @property
    def is_on(self) -> bool:
        return self.__is_on

    @is_on.setter
    def is_on(self, value: bool) -> None:
        self.__is_on = value
        # on change la texture selon l'état
        if self.__is_on:
            self.texture = TEXTURE_SWITCH_ON
        else:
            self.texture = TEXTURE_SWITCH_OFF

    def inverse_state_switch(self) -> None:
        self.is_on = not self.is_on


# sprite de porte : bloque le passage quand fermee, laisse passer quand ouverte
class GateSprite(arcade.Sprite):
    open_if: Final[object]
    __is_open: bool

    def __init__(self, gate_data: GateData) -> None:
        super().__init__(
            TEXTURE_GATE_CLOSED,
            scale=SCALE,
            center_x=grid_to_pixels(gate_data.x),
            center_y=grid_to_pixels(gate_data.y),
        )
        self.open_if = gate_data.open_if
        self.__is_open = False

    @property
    def is_open(self) -> bool:
        return self.__is_open

    @is_open.setter
    def is_open(self, value: bool) -> None:
        self.__is_open = value
        self.texture = TEXTURE_GATE_OPEN if value else TEXTURE_GATE_CLOSED


# regroupe tous les sprites lists du monde (sol, murs, objets, ennemis)
@dataclass
class WorldSprites:
    grounds: arcade.SpriteList[arcade.Sprite]
    walls: arcade.SpriteList[arcade.Sprite]
    crystals: arcade.SpriteList[arcade.TextureAnimationSprite]
    keys: arcade.SpriteList[arcade.TextureAnimationSprite]
    chests: arcade.SpriteList[arcade.TextureAnimationSprite]
    spikes: arcade.SpriteList[arcade.TextureAnimationSprite]
    spinners: arcade.SpriteList[SpinnerSprite]
    holes: arcade.SpriteList[arcade.Sprite]
    enemies: arcade.SpriteList
    all_enemies: arcade.SpriteList


# regroupe les sprite lists des elements interactifs (switchs et portes)
@dataclass
class InteractionSprites:
    switches: arcade.SpriteList[SwitchSprite]
    gates: arcade.SpriteList[GateSprite]


# construit les switchs et portes depuis la map
def switch_gate_interactions(
    game_map: Map,
    walls: arcade.SpriteList[arcade.Sprite],
) -> InteractionSprites:
    switches = arcade.SpriteList()
    gates = arcade.SpriteList()

    for switch_data in game_map.switches:
        switches.append(SwitchSprite(switch_data))

    for gate_data in game_map.gates:
        gate = GateSprite(gate_data)
        gates.append(gate)
        walls.append(gate)

    update_gate_states(switches, gates, walls)
    return InteractionSprites(switches=switches, gates=gates)


def compute_horizontal_spinner_limits(game_map: Map, start_x: int, start_y: int) -> tuple[int, int]:
    """Retourne (left_x, right_x) en coordonnées grille : les colonnes extrêmes que le spinner peut atteindre
    sur sa ligne, en s'arrêtant juste avant les buissons ou les bords de la carte."""
    left_x = start_x
    i = start_x - 1
    while i >= 0:
        if game_map.get(i, start_y) == GridCell.BUSH:
            break
        left_x = i
        i -= 1

    right_x = start_x
    i = start_x + 1
    while i < game_map.width:
        if game_map.get(i, start_y) == GridCell.BUSH:
            break
        right_x = i
        i += 1

    return (left_x, right_x)


def compute_vertical_spinner_limits(game_map: Map, start_x: int, start_y: int) -> tuple[int, int]:
    """Retourne (bottom_y, top_y) en coordonnées grille : les lignes extrêmes que le spinner peut atteindre
    sur sa colonne, en s'arrêtant juste avant les buissons ou les bords de la carte."""
    bottom_y = start_y
    i = start_y - 1
    while i >= 0:
        if game_map.get(start_x, i) == GridCell.BUSH:
            break
        bottom_y = i
        i -= 1

    top_y = start_y
    i = start_y + 1
    while i < game_map.height:
        if game_map.get(start_x, i) == GridCell.BUSH:
            break
        top_y = i
        i += 1

    return (bottom_y, top_y)


# cree un spinner et calcule ses limites de deplacement selon son orientation
def make_spinner(game_map: Map, x: int, y: int, is_horizontal: bool) -> SpinnerSprite:
    if is_horizontal:
        left_x, right_x = compute_horizontal_spinner_limits(game_map, x, y)
        min_pos = grid_to_pixels(left_x)
        max_pos = grid_to_pixels(right_x)
    else:
        bottom_y, top_y = compute_vertical_spinner_limits(game_map, x, y)
        min_pos = grid_to_pixels(bottom_y)
        max_pos = grid_to_pixels(top_y)

    return SpinnerSprite(
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
        is_horizontal=is_horizontal,
        min_pos=min_pos,
        max_pos=max_pos,
    )


# parcourt toute la grille et associe les sprites correspondant a chaque cellule
def build_world(game_map: Map) -> WorldSprites:
    grounds = arcade.SpriteList(use_spatial_hash=True)
    walls = arcade.SpriteList(use_spatial_hash=True)
    crystals = arcade.SpriteList(use_spatial_hash=True)
    keys = arcade.SpriteList(use_spatial_hash=True)
    chests = arcade.SpriteList(use_spatial_hash=True)
    spikes = arcade.SpriteList(use_spatial_hash=True)
    spinners = arcade.SpriteList()
    holes = arcade.SpriteList()
    enemies = arcade.SpriteList()
    all_enemies = arcade.SpriteList()

    for x in range(game_map.width):
        for y in range(game_map.height):
            grounds.append(make_tile_sprite(TEXTURE_GRASS, x, y))
            cell = game_map.get(x, y)

            if cell == GridCell.BUSH:
                walls.append(make_tile_sprite(TEXTURE_BUSH, x, y))

            elif cell == GridCell.CRYSTAL:
                crystals.append(make_tile_animation_sprite(ANIMATION_CRYSTALS, x, y))

            elif cell == GridCell.KEY:
                keys.append(make_tile_animation_sprite(ANIMATION_KEY, x, y))

            elif cell == GridCell.CHEST:
                chests.append(make_tile_animation_sprite(ANIMATION_CHEST, x, y))

            elif cell == GridCell.SPIKES:
                spikes.append(make_tile_animation_sprite(ANIMATION_SPIKES, x, y))

            elif cell == GridCell.SPINNER_HORIZONTAL or cell == GridCell.SPINNER_VERTICAL:
                spinner = make_spinner(
                    game_map,
                    x,
                    y,
                    is_horizontal=(cell == GridCell.SPINNER_HORIZONTAL),
                )
                spinners.append(spinner)
                all_enemies.append(spinner)

            elif cell == GridCell.HOLE:
                holes.append(make_tile_sprite(TEXTURE_HOLE, x, y))

            elif cell == GridCell.BAT:
                bat = Bat(
                    start_x=grid_to_pixels(x),
                    start_y=grid_to_pixels(y),
                    world_width=game_map.width * TILE_SIZE,
                    world_height=game_map.height * TILE_SIZE,
                )
                enemies.append(bat)
                all_enemies.append(bat)

            elif cell == GridCell.BLOB:
                blob = Blob(
                    start_x=grid_to_pixels(x),
                    start_y=grid_to_pixels(y),
                    world_width=game_map.width * TILE_SIZE,
                    world_height=game_map.height * TILE_SIZE,
                )
                enemies.append(blob)
                all_enemies.append(blob)

    return WorldSprites(
        grounds=grounds,
        walls=walls,
        crystals=crystals,
        keys=keys,
        chests=chests,
        spikes=spikes,
        spinners=spinners,
        holes=holes,
        enemies=enemies,
        all_enemies=all_enemies,
    )
