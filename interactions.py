from math import sqrt
import arcade

from constants import SPIKES_SWITCH_TIME
from gate_conditions import condition_is_true
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
    # On cherche tous les interrupteurs actuellement touches par l'arme
    hit_switches = arcade.check_for_collision_with_list(weapon, switches)

    # On garde seulement leurs ids, pour memoriser quels interrupteurs
    hit_ids = {switch.id for switch in hit_switches}

    # Ce booleen dit si l'arme vient de toucher au moins un nouveau switch
    # Il sert surtout au boomerang, qui doit revenir apres un nouveau contact
    has_new_hit = False

    for switch in hit_switches:
        if switch.id not in already_touched:
            switch.inverse_state_switch()
            has_new_hit = True

    # On renvoie les ids touches maintenant, et si au moins un nouveau switch
    # a ete activé
    return (hit_ids, has_new_hit)


def update_switches_hit_by_sword(
    sword: Sword,
    sword_touched_switches: set[str],
    switches: arcade.SpriteList,
) -> set[str]:
    # Si l'epee n'est pas active, elle ne peut pas toucher d'interrupteur
    if not sword.active:
        return set()

    # On inverse les interrupteurs touches par l'epee
    # Le deuxieme resultat n'est pas utilise pour l'épee on l'ignore avec _
    new_touched, _ = inverse_state_switch_hit_switches(sword, switches, sword_touched_switches)
    return new_touched


def update_switches_hit_by_boomerang(
    boomerang: Boomerang,
    boomerang_touched_switches: set[str],
    switches: arcade.SpriteList,
) -> set[str]:
    # Si le boomerang est inactif, il n'est pas visible et ne touche rien
    if boomerang.state == BoomerangState.INACTIVE:
        return set()

    # On inverse les interrupteurs touches par le boomerang
    # has_new_hit indique s'il vient d'activer un nouveau switch.
    (hit_ids, has_new_hit) = inverse_state_switch_hit_switches(boomerang, switches, boomerang_touched_switches)

    # Pendant le lancement, toucher un interrupteur fait revenir le boomerang,
    # comme quand il touche un mur ou un ennemi
    if has_new_hit and boomerang.state == BoomerangState.LAUNCHING:
        boomerang.start_return()

    # On renvoie les ids touches pour eviter de rebasculer les memes switches
    # tant que le boomerang reste dessus.
    return hit_ids
