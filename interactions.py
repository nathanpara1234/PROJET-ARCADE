from math import sqrt
import arcade

from constants import SPIKES_SWITCH_TIME
from gate_conditions import condition_is_true
from player import Player
from weapons import Boomerang, Sword, BoomerangState


# renvoie True si le joueur doit recommencer la salle
def should_restart_after_collision(
    player: Player,
    enemies: arcade.SpriteList,
    holes: arcade.SpriteList,
) -> bool:
    if arcade.check_for_collision_with_list(player, enemies) and not player.indestructible:
        return True
    elif player.indestructible:
        # joueur invincible : on supprime les ennemis touchés
        for enemy in arcade.check_for_collision_with_list(player, enemies):
            enemy.remove_from_sprite_lists()

    for hole in holes:
        # on regarde si le joueur est trop proche d'un trou
        distance = sqrt((player.center_x - hole.center_x) ** 2 + (player.center_y - hole.center_y) ** 2)
        if distance <= 16:
            return True

    return False


# gère l'état des piques (actives/inactives) en fonction du timer
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
                 spike.alpha = 100  # on les rend transparents quand inactifs

    return (spikes_timer, spikes_are_active)


# True si le joueur touche des piques actives
def should_restart_after_spikes_collision(
    spikes_are_active: bool,
    player: Player,
    spikes: arcade.SpriteList,
) -> bool:
    if not spikes_are_active or player.indestructible:
        return False
    return bool(arcade.check_for_collision_with_list(player, spikes))


# Met à jour l'état des portes en fonction des interrupteurs
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
        gate.is_open = gate_should_be_open

        if gate.is_open:
            # porte ouverte : retire du mur pour laisser passer le joueur
            if gate in walls:
                walls.remove(gate)
        else:
            # porte fermee : ajoute aux murs pour bloquer le joueur
            if gate not in walls:
                walls.append(gate)


def inverse_state_switch_hit_switches(
    weapon: arcade.Sprite,
    switches: arcade.SpriteList,
    already_touched: set[str],
) -> tuple[set[str], bool]:
    hit_switches = arcade.check_for_collision_with_list(weapon, switches)
    # on récupère les ids des switches touchés pour savoir lesquels étaient déjà actifs
    hit_ids = {switch.id for switch in hit_switches}
    has_new_hit = False

    for switch in hit_switches:
        # on inverse seulement si le switch n'était pas déjà touché à la frame précédente
        if switch.id not in already_touched:
            switch.inverse_state_switch()
            has_new_hit = True

    # has_new_hit permet au boomerang de savoir s'il doit revenir
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
    # le deuxieme resultat (has_new_hit) n'est pas utilisé pour l'épée
    result = inverse_state_switch_hit_switches(sword, switches, sword_touched_switches)
    return result[0]


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
    # comme pour les murs
    if has_new_hit and boomerang.state == BoomerangState.LAUNCHING:
        boomerang.start_return()

    # On renvoie les ids touches pour eviter de rebasculer les memes switches
    # tant que le boomerang reste dessus
    return hit_ids
