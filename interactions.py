from math import sqrt
from typing import Callable
import arcade

from constants import SPIKES_SWITCH_TIME
from gate_conditions import condition_is_true
from player import Player
from weapons import Boomerang, Sword, BoomerangState


def restart_if_collision(
    player: Player,
    enemies: arcade.SpriteList,
    holes: arcade.SpriteList,
    restart: Callable[[], None],
) -> None:
    if arcade.check_for_collision_with_list(player, enemies) and not player.indestructible:
        restart()
    elif player.indestructible:
        for enemy in arcade.check_for_collision_with_list(player, enemies):
            enemy.remove_from_sprite_lists()
    for hole in holes:
        distance = sqrt((player.center_x - hole.center_x) ** 2 + (player.center_y - hole.center_y) ** 2)
        if distance <= 16:
            restart()
            return


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
            spike.alpha = 255 if spikes_are_active else 100

    return spikes_timer, spikes_are_active


def restart_if_spikes_collision(
    spikes_are_active: bool,
    player: Player,
    spikes: arcade.SpriteList,
    restart: Callable[[], None],
) -> None:
    if not spikes_are_active:
        return
    if arcade.check_for_collision_with_list(player, spikes):
        restart()


def update_gate_states(
    switches: arcade.SpriteList,
    gates: arcade.SpriteList,
    walls: arcade.SpriteList,
) -> None:
    switch_states = {}
    for switch in switches:
        switch_states[switch.id] = switch.is_on

    for gate in gates:
        gate_should_be_open = condition_is_true(gate.open_if, switch_states)
        gate.set_open(gate_should_be_open)

        if gate.is_open:
            if gate in walls:
                walls.remove(gate)
        else:
            if gate not in walls:
                walls.append(gate)


def inverse_state_switch_hit_switches(
    weapon: arcade.Sprite,
    switches: arcade.SpriteList,
    already_touched: set[str],
) -> tuple[set[str], bool]:
    hit_switches = arcade.check_for_collision_with_list(weapon, switches)
    hit_ids = {switch.id for switch in hit_switches}
    has_new_hit = False

    for switch in hit_switches:
        if switch.id not in already_touched:
            switch.inverse_state_switch()
            has_new_hit = True

    return hit_ids, has_new_hit


def update_switches_hit_by_sword(
    sword: Sword,
    sword_touched_switches: set[str],
    switches: arcade.SpriteList,
) -> set[str]:
    if not sword.active:
        return set()

    new_touched, _ = inverse_state_switch_hit_switches(sword, switches, sword_touched_switches)
    return new_touched


def update_switches_hit_by_boomerang(
    boomerang: Boomerang,
    boomerang_touched_switches: set[str],
    switches: arcade.SpriteList,
) -> set[str]:
    if boomerang.state == BoomerangState.INACTIVE:
        return set()

    hit_ids, has_new_hit = inverse_state_switch_hit_switches(boomerang, switches, boomerang_touched_switches)

    if has_new_hit and boomerang.state == BoomerangState.LAUNCHING:
        boomerang.start_return()

    return hit_ids
