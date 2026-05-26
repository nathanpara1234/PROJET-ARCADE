from dataclasses import dataclass
import arcade

from constants import TILE_SIZE, SCALE, SPINNER_SPEED
from enemies import Bat, Blob, SpinnerSprite, compute_horizontal_spinner_limits, compute_vertical_spinner_limits
from map import Map, GridCell
from sprite import (
    GateSprite,
    SwitchSprite,
    make_tile_sprite,
    make_tile_animation_sprite,
    grid_to_pixels,
)
from interactions import update_gate_states
from textures import (
    TEXTURE_GRASS,
    TEXTURE_BUSH,
    TEXTURE_HOLE,
    ANIMATION_CRYSTALS,
    ANIMATION_KEY,
    ANIMATION_CHEST,
    ANIMATION_SPIKES,
    ANIMATION_SPINNER,
)


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


@dataclass
class InteractionSprites:
    switches: arcade.SpriteList[SwitchSprite]
    gates: arcade.SpriteList[GateSprite]


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


def make_spinner(game_map: Map, x: int, y: int, is_horizontal: bool) -> SpinnerSprite:
    spinner = SpinnerSprite(
        animation=ANIMATION_SPINNER,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )

    spinner.is_horizontal = is_horizontal

    if is_horizontal:
        left_x, right_x = compute_horizontal_spinner_limits(game_map, x, y)
        spinner.min_pos = grid_to_pixels(left_x)
        spinner.max_pos = grid_to_pixels(right_x)
        spinner.change_x = SPINNER_SPEED
        spinner.change_y = 0
    else:
        bottom_y, top_y = compute_vertical_spinner_limits(game_map, x, y)
        spinner.min_pos = grid_to_pixels(bottom_y)
        spinner.max_pos = grid_to_pixels(top_y)
        spinner.change_x = 0
        spinner.change_y = SPINNER_SPEED

    return spinner


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
