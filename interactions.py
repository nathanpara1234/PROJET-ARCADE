from math import sqrt
import arcade

from constants import SPIKES_SWITCH_TIME
from player import Player
from weapons import Boomerang, Sword, BoomerangState


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
