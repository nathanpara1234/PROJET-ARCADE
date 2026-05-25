from dataclasses import dataclass
import arcade

from constants import TILE_SIZE, SCALE, SPINNER_SPEED
from enemies import Bat, Blob, SpinnerSprite, compute_horizontal_spinner_limits, compute_vertical_spinner_limits
from map import Map, GridCell
from sprite import make_tile_sprite, make_tile_animation_sprite, grid_to_pixels
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

            elif cell == GridCell.SPINNER_HORIZONTAL:
                spinner = SpinnerSprite(
                    animation=ANIMATION_SPINNER,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                spinner.is_horizontal = True
                left_x, right_x = compute_horizontal_spinner_limits(game_map, x, y)
                spinner.min_pos = grid_to_pixels(left_x)
                spinner.max_pos = grid_to_pixels(right_x)
                spinner.change_x = SPINNER_SPEED
                spinner.change_y = 0
                spinners.append(spinner)
                all_enemies.append(spinner)

            elif cell == GridCell.SPINNER_VERTICAL:
                spinner = SpinnerSprite(
                    animation=ANIMATION_SPINNER,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                spinner.is_horizontal = False
                bottom_y, top_y = compute_vertical_spinner_limits(game_map, x, y)
                spinner.min_pos = grid_to_pixels(bottom_y)
                spinner.max_pos = grid_to_pixels(top_y)
                spinner.change_x = 0
                spinner.change_y = SPINNER_SPEED
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
