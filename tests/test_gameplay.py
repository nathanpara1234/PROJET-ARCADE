import arcade

from constants import SPIKES_SWITCH_TIME
from gameview import GameView
from interactions import update_spikes
from map import load_map_from_string
from weapons import BoomerangState
from world_builder import grid_to_pixels


def make_spikes_view(window: arcade.Window) -> GameView:
    game_map = load_map_from_string(
"""width: 5
height: 5
---
xxxxx
x   x
x ! x
x P x
xxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    return view


def test_player_collects_crystals(window: arcade.Window) -> None:
    """quand le joueur marche sur un cristal, il doit disparaitre de la map"""
    game_map = load_map_from_string(
"""width: 8
height: 5
---
xxxxxxxx
x      x
x  *   x
x P**  x
xxxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)

    INITIAL_CRYSTAL_COUNT = 3

    assert len(view.world.crystals) == INITIAL_CRYSTAL_COUNT

    crystal = view.world.crystals[0]
    view.player.position = crystal.position
    view.do_on_update(1 / 60)

    assert len(view.world.crystals) == INITIAL_CRYSTAL_COUNT - 1
    assert view.player.score == 1

    crystal = view.world.crystals[0]
    view.player.position = crystal.position
    view.do_on_update(1 / 60)
    assert view.player.score == 2

    assert len(view.world.crystals) == INITIAL_CRYSTAL_COUNT - 2


def test_player_touching_active_spikes_restarts(window: arcade.Window) -> None:
    """Verifie que les pics actifs font perdre le joueur"""
    view = make_spikes_view(window)
    spike = view.world.spikes[0]

    view.player.center_x = spike.center_x
    view.player.center_y = spike.center_y
    view.spikes_are_active = True
    view.do_on_update(1 / 60)

    assert window.current_view is not view


def test_player_touching_inactive_spikes_survives(window: arcade.Window) -> None:
    """le joueur peut marcher sur des pics inactifs sans mourir"""
    view = make_spikes_view(window)
    spike = view.world.spikes[0]

    view.player.center_x = spike.center_x
    view.player.center_y = spike.center_y
    view.spikes_are_active = False
    view.do_on_update(1 / 60)

    assert window.current_view is view


def test_spikes_timer_switches_from_active_to_inactive(window: arcade.Window) -> None:
    """apres SPIKES_SWITCH_TIME secondes, les pics actifs passent en inactif"""
    view = make_spikes_view(window)

    spikes_timer, spikes_are_active = update_spikes(
        view.world.spikes,
        spikes_timer=SPIKES_SWITCH_TIME,
        spikes_are_active=True,
        delta_time=0,
    )

    assert spikes_timer == 0.0
    assert not spikes_are_active
    assert view.world.spikes[0].alpha == 100


def test_spikes_timer_switches_from_inactive_to_active(window: arcade.Window) -> None:
    """Verifie que les pics redeviennent actifs apres le delai"""
    view = make_spikes_view(window)

    spikes_timer, spikes_are_active = update_spikes(
        view.world.spikes,
        spikes_timer=SPIKES_SWITCH_TIME,
        spikes_are_active=False,
        delta_time=0,
    )

    assert spikes_timer == 0.0
    assert spikes_are_active
    assert view.world.spikes[0].alpha == 255


def test_player_can_walk_between_separated_holes(window: arcade.Window) -> None:
    """deux trous separes par une case : le joueur peut passer entre eux"""
    game_map = load_map_from_string(
"""width: 7
height: 5
---
xxxxxxx
x     x
x O O x
x P   x
xxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)

    view.player.center_x = grid_to_pixels(3)
    view.player.center_y = grid_to_pixels(2)
    view.do_on_update(1 / 60)

    assert window.current_view is view


def test_player_falls_between_adjacent_holes(window: arcade.Window) -> None:
    """Verifie que le joueur tombe quand il passe entre deux trous colles"""
    game_map = load_map_from_string(
"""width: 7
height: 5
---
xxxxxxx
x     x
x OO  x
x P   x
xxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)

    view.player.center_x = (grid_to_pixels(2) + grid_to_pixels(3)) / 2
    view.player.center_y = grid_to_pixels(2)
    view.do_on_update(1 / 60)

    assert window.current_view is not view


def make_switch_gate_view(window: arcade.Window) -> GameView:
    game_map = load_map_from_string(
"""width: 7
height: 5
switches:
  - id: first
    x: 2
    y: 2
gates:
  - x: 4
    y: 2
    open_if:
      switch_is_on: first
---
xxxxxxx
x     x
x ^ | x
x P   x
xxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    return view


def test_gate_starts_closed_when_switch_is_off(window: arcade.Window) -> None:
    """au depart, si le switch est off, le portail doit bloquer le joueur"""
    view = make_switch_gate_view(window)
    gate = view.interactions.gates[0]

    assert not gate.is_open
    assert gate in view.world.walls


def test_gate_starts_open_when_switch_is_on(window: arcade.Window) -> None:
    """Verifie qu'un portail commence ouvert si sa condition est deja vraie"""
    game_map = load_map_from_string(
"""width: 7
height: 5
switches:
  - id: first
    x: 2
    y: 2
    state: on
gates:
  - x: 4
    y: 2
    open_if:
      switch_is_on: first
---
xxxxxxx
x     x
x ^ | x
x P   x
xxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    gate = view.interactions.gates[0]

    assert gate.is_open
    assert gate not in view.world.walls


def test_sword_toggles_switch_and_opens_gate(window: arcade.Window) -> None:
    """Verifie que l'epee active un interrupteur et ouvre son portail"""
    view = make_switch_gate_view(window)
    switch = view.interactions.switches[0]
    gate = view.interactions.gates[0]

    view.sword.active = True
    view.sword.visible = True

    view.sword.center_x = switch.center_x
    view.sword.center_y = switch.center_y
    view.do_on_update(1 / 60)

    assert switch.is_on
    assert gate.is_open
    assert gate not in view.world.walls


def test_boomerang_toggles_switch_and_returns(window: arcade.Window) -> None:
    """Verifie que le boomerang active un interrupteur et revient"""
    view = make_switch_gate_view(window)
    switch = view.interactions.switches[0]
    gate = view.interactions.gates[0]

    view.boomerang.launch(view.player)
    view.boomerang.center_x = switch.center_x
    view.boomerang.center_y = switch.center_y
    view.boomerang.change_x = 0
    view.boomerang.change_y = 0
    view.do_on_update(1 / 60)

    assert switch.is_on
    assert gate.is_open
    assert gate not in view.world.walls
    assert view.boomerang.state == BoomerangState.RETURNING


def make_key_chest_view(window: arcade.Window) -> GameView:
    game_map = load_map_from_string(
"""width: 7
height: 5
---
xxxxxxx
x k   x
x C   x
x P   x
xxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    return view


def test_chest_with_key_makes_player_invincible(window: arcade.Window) -> None:
    """Verifie qu'ouvrir un coffre avec une cle rend le joueur invincible"""
    view = make_key_chest_view(window)
    key = view.world.keys[0]
    chest = view.world.chests[0]
    # ramasse la cle
    view.player.center_x = key.center_x
    view.player.center_y = key.center_y
    view.do_on_update(1 / 60)
    assert view.player.key == 1
    # ouvre le coffre
    view.player.center_x = chest.center_x
    view.player.center_y = chest.center_y
    view.do_on_update(1 / 60)
    assert view.player.indestructible
    assert view.player.key == 0


def test_chest_stays_closed_without_key(window: arcade.Window) -> None:
    """sans cle, toucher un coffre ne doit rien faire"""
    view = make_key_chest_view(window)
    chest = view.world.chests[0]
    view.player.center_x = chest.center_x
    view.player.center_y = chest.center_y
    view.do_on_update(1 / 60)
    assert not view.player.indestructible
    assert view.player.key == 0


def test_invincible_player_safe_on_spikes(window: arcade.Window) -> None:
    """un joueur invincible peut marcher sur des piques actives sans perdre"""
    view = make_spikes_view(window)
    spike = view.world.spikes[0]
    view.player.player_become_indestructible()
    view.player.center_x = spike.center_x
    view.player.center_y = spike.center_y
    view.spikes_are_active = True
    view.do_on_update(1 / 60)
    assert window.current_view is view


def test_invincible_player_kills_bat(window: arcade.Window) -> None:
    """Verifie que le joueur invincible tue les ennemis en les touchant"""
    game_map = load_map_from_string(
"""width: 7
height: 5
---
xxxxxxx
x     x
x  v  x
x  P  x
xxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    view.player.player_become_indestructible()
    bat = view.world.enemies[0]
    view.player.center_x = bat.center_x
    view.player.center_y = bat.center_y
    nb_ennemis = len(view.world.enemies)
    view.do_on_update(1 / 60)
    assert len(view.world.enemies) == nb_ennemis - 1
    assert window.current_view is view


def test_player_picks_up_key(window: arcade.Window) -> None:
    """ramasser une cle doit incrementer le compteur et retirer la cle de la map"""
    game_map = load_map_from_string(
"""width: 5
height: 5
---
xxxxx
x   x
x k x
x P x
xxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    key = view.world.keys[0]
    view.player.center_x = key.center_x
    view.player.center_y = key.center_y
    view.do_on_update(1 / 60)
    assert view.player.key == 1
    assert len(view.world.keys) == 0


def test_switch_changes_state(window: arcade.Window) -> None:
    """inverse_state_switch doit alterner l'etat du switch a chaque appel"""
    view = make_switch_gate_view(window)
    switch = view.interactions.switches[0]
    assert not switch.is_on
    switch.inverse_state_switch()
    assert switch.is_on
    switch.inverse_state_switch()
    assert not switch.is_on


def test_switch_ne_rebascule_pas_si_epee_reste_dessus(window: arcade.Window) -> None:
    """si l'épée reste sur le switch entre deux frames il doit pas rebaculer"""
    view = make_switch_gate_view(window)
    switch = view.interactions.switches[0]
    view.sword.active = True
    view.sword.visible = True
    view.sword.center_x = switch.center_x
    view.sword.center_y = switch.center_y
    view.do_on_update(1 / 60)  # premier contact, switch s'allume
    assert switch.is_on
    view.do_on_update(1 / 60)  # l'épée est encore là, doit pas re-basculer
    assert switch.is_on


def test_switch_does_not_block_player(window: arcade.Window) -> None:
    """Verifie qu'un interrupteur n'est pas un mur pour le joueur"""
    view = make_switch_gate_view(window)
    switch = view.interactions.switches[0]

    view.player.center_x = switch.center_x
    view.player.center_y = switch.center_y
    view.do_on_update(1 / 60)

    assert switch not in view.world.walls
    assert window.current_view is view


def test_gate_and_opens_only_when_both_switches_on(window: arcade.Window) -> None:
    """une gate avec and ne s'ouvre que si les deux switches sont actives"""
    game_map = load_map_from_string(
        """
        width: 9
        height: 5
        switches:
          - id: a
            x: 2
            y: 2
          - id: b
            x: 6
            y: 2
        gates:
          - x: 4
            y: 2
            open_if:
              and:
                - switch_is_on: a
                - switch_is_on: b
        ---
        xxxxxxxxx
        x       x
        x ^ | ^ x
        x P     x
        xxxxxxxxx
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    switch_a = view.interactions.switches[0]
    switch_b = view.interactions.switches[1]
    gate = view.interactions.gates[0]

    assert not gate.is_open

    switch_a.inverse_state_switch()
    view.do_on_update(1 / 60)
    assert not gate.is_open

    switch_b.inverse_state_switch()
    view.do_on_update(1 / 60)
    assert gate.is_open


def test_gate_or_opens_with_one_switch(window: arcade.Window) -> None:
    """une gate avec or s'ouvre des qu'un des deux switches est active"""
    game_map = load_map_from_string(
        """
        width: 9
        height: 5
        switches:
          - id: a
            x: 2
            y: 2
          - id: b
            x: 6
            y: 2
        gates:
          - x: 4
            y: 2
            open_if:
              or:
                - switch_is_on: a
                - switch_is_on: b
        ---
        xxxxxxxxx
        x       x
        x ^ | ^ x
        x P     x
        xxxxxxxxx
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    switch_a = view.interactions.switches[0]
    gate = view.interactions.gates[0]

    assert not gate.is_open

    switch_a.inverse_state_switch()
    view.do_on_update(1 / 60)
    assert gate.is_open


def test_gate_not_open_when_switch_off(window: arcade.Window) -> None:
    """une gate avec not est ouverte quand le switch est off et fermee quand il est on"""
    game_map = load_map_from_string(
        """
        width: 7
        height: 5
        switches:
          - id: a
            x: 2
            y: 2
        gates:
          - x: 4
            y: 2
            open_if:
              not:
                - switch_is_on: a
        ---
        xxxxxxx
        x     x
        x ^ | x
        x P   x
        xxxxxxx
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    switch = view.interactions.switches[0]
    gate = view.interactions.gates[0]

    assert gate.is_open

    switch.inverse_state_switch()
    view.do_on_update(1 / 60)
    assert not gate.is_open
