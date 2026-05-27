from math import sqrt
import arcade
from textures import TEXTURE_EMPTY_CHEST
from constants import SPIKES_SWITCH_TIME
from player import Player
from weapons import Boomerang, Sword, BoomerangState
from text import Text


def should_restart_after_collision(
    player: Player,
    enemies: arcade.SpriteList,
    holes: arcade.SpriteList,
) -> bool:
    if arcade.check_for_collision_with_list(player, enemies) and not player.indestructible:
        return True
    elif player.indestructible:
        for enemy in arcade.check_for_collision_with_list(player, enemies):
            enemy.remove_from_sprite_lists()

    for hole in holes:
        distance = sqrt((player.center_x - hole.center_x) ** 2 + (player.center_y - hole.center_y) ** 2)
        if distance <= 16:
            return True

    return False


def update_spikes(
    spikes: arcade.SpriteList,
    spikes_timer: float,
    spikes_are_active: bool,
    delta_time: float,
) -> tuple[float, bool]:
    spikes.update_animation()
    spikes_timer += delta_time

    if spikes_timer >= SPIKES_SWITCH_TIME:
        spikes_timer = 0.0
        spikes_are_active = not spikes_are_active
        for spike in spikes:
            if spikes_are_active:
                 spike.alpha = 255
            else:
                 spike.alpha = 100

    return (spikes_timer, spikes_are_active)


def should_restart_after_spikes_collision(
    spikes_are_active: bool,
    player: Player,
    spikes: arcade.SpriteList,
) -> bool:
    if not spikes_are_active:
        return False
    return bool(arcade.check_for_collision_with_list(player, spikes))

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
