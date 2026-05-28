from math import sqrt
import networkx as nx
import arcade

from constants import TILE_SIZE
from textures import TEXTURE_EMPTY_CHEST
from player import Player
from text import Text


def _clamp_camera(pos: float, window_size: float, world_size: float) -> float:# soit ça retourne la position du joueur ou une limite de map
    min_camera = window_size / 2
    max_camera = world_size - window_size / 2
    if pos < min_camera:
        return min_camera
    elif pos > max_camera:
        return max_camera
    return pos


def update_camera_position(# soit la caméra suit le joueur soit elle est bloqué à la limite
    camera: arcade.camera.Camera2D,
    player: Player,
    window: arcade.Window,
    world_width: int,
    world_height: int,
) -> None:
    camera.position = (
        _clamp_camera(player.center_x, window.width, world_width),
        _clamp_camera(player.center_y, window.height, world_height),
    )


def update_enemies(# pour savoir si le player est dans la zone du blob
    spinners: arcade.SpriteList,
    enemies: arcade.SpriteList,
    player: Player,
    walls: arcade.SpriteList,
    navmesh: nx.Graph,
) -> None:
    for spinner in spinners:
        spinner.spinner_move()

    for enemy in enemies:
        distance = sqrt((enemy.center_x - player.center_x) ** 2 + (enemy.center_y - player.center_y) ** 2)
        if distance <= 5 * TILE_SIZE and arcade.has_line_of_sight(enemy.position, player.position, walls):
            enemy.move(navmesh, player.position)
        else:
            enemy.move(navmesh, None)


def update_collectibles(# fonction de collision avec item recuperable
    player: Player,
    crystals: arcade.SpriteList,
    crystal_sound: arcade.Sound,
    keys: arcade.SpriteList,
    keys_sound: arcade.Sound,
    chests: arcade.SpriteList,
    chests_sound: arcade.Sound,
    text: Text,
) -> None:
    collision_crystals = arcade.check_for_collision_with_list(player, crystals)
    for crystal in collision_crystals:

        crystal.remove_from_sprite_lists()
        arcade.play_sound(crystal_sound)
        player.score += 1
        text.update_score(player)
        if player.score >= text.total_crystals:
            text.show_end()

    collision_keys = arcade.check_for_collision_with_list(player, keys)
    for key in collision_keys:
        key.remove_from_sprite_lists()
        arcade.play_sound(keys_sound)
        player.key += 1
        text.update_keys(player)

    collision_chests = arcade.check_for_collision_with_list(player, chests)
    for chest in collision_chests:
        if player.key > 0:
            chest.texture = TEXTURE_EMPTY_CHEST
            arcade.play_sound(chests_sound)
            player.key -= 1
            text.update_keys(player)
            player.player_become_indestructible()
