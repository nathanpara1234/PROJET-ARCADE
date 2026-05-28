# --- test_conftest.py ---
import arcade

from constants import SPIKES_SWITCH_TIME
from gameview import GameView
from interactions import update_spikes
from map import load_map_from_string
from weapons import BoomerangState


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
    """Verifie que le joueur retire les cristaux touches de la map"""
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

    assert len(view.crystals) == INITIAL_CRYSTAL_COUNT

    crystal = view.crystals[0]
    view.player.position = crystal.position
    view.do_on_update(1 / 60)

    assert len(view.crystals) == INITIAL_CRYSTAL_COUNT - 1

    crystal = view.crystals[0]
    view.player.position = crystal.position
    view.do_on_update(1 / 60)

    assert len(view.crystals) == INITIAL_CRYSTAL_COUNT - 2


def test_player_touching_active_spikes_restarts(window: arcade.Window) -> None:
    """Verifie que les pics actifs font perdre le joueur"""
    view = make_spikes_view(window)
    spike = view.spikes[0]

    view.player.center_x = spike.center_x
    view.player.center_y = spike.center_y
    view.spikes_are_active = True
    view.do_on_update(1 / 60)

    assert window.current_view is not view


def test_player_touching_inactive_spikes_survives(window: arcade.Window) -> None:
    """Verifie que les pics inactifs ne font pas perdre le joueur"""
    view = make_spikes_view(window)
    spike = view.spikes[0]

    view.player.center_x = spike.center_x
    view.player.center_y = spike.center_y
    view.spikes_are_active = False
    view.do_on_update(1 / 60)

    assert window.current_view is view


def test_spikes_timer_switches_from_active_to_inactive(window: arcade.Window) -> None:
    """Verifie que le timer des pics alterne l'etat actif/inactif"""
    view = make_spikes_view(window)

    spikes_timer, spikes_are_active = update_spikes(
        view.spikes,
        spikes_timer=SPIKES_SWITCH_TIME,
        spikes_are_active=True,
        delta_time=0,
    )

    assert spikes_timer == 0.0
    assert not spikes_are_active
    assert view.spikes[0].alpha == 100


def test_spikes_timer_switches_from_inactive_to_active(window: arcade.Window) -> None:
    """Verifie que les pics redeviennent actifs apres le delai"""
    view = make_spikes_view(window)

    spikes_timer, spikes_are_active = update_spikes(
        view.spikes,
        spikes_timer=SPIKES_SWITCH_TIME,
        spikes_are_active=False,
        delta_time=0,
    )

    assert spikes_timer == 0.0
    assert spikes_are_active
    assert view.spikes[0].alpha == 255


# Test Trou
import arcade

from gameview import GameView
from map import load_map_from_string
from world_builder import grid_to_pixels


def test_player_can_walk_between_separated_holes(window: arcade.Window) -> None:
    """Verifie que le joueur peut passer entre deux trous separes par une case"""
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


def test_sword_opens_gate_by_hitting_switch(window: arcade.Window) -> None:
    """Verifie que l'epee active un interrupteur et ouvre le portail lie"""
    game_map = load_map_from_string(
        """
        width: 7
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
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    switch = view.switches[0]
    gate = view.gates[0]

    assert not switch.is_on
    assert not gate.is_open
    assert gate in view.walls

    view.sword.active = True
    view.sword.visible = True
    view.sword.elapsed_time = 0
    view.sword.center_x = switch.center_x
    view.sword.center_y = switch.center_y
    view.do_on_update(1 / 60)

    assert switch.is_on
    assert gate.is_open
    assert gate not in view.walls


def test_gate_starts_open_when_switch_state_is_on(window: arcade.Window) -> None:
    """Verifie qu'un portail est ouvert des le debut si sa condition est vraie"""
    game_map = load_map_from_string(
        """
        width: 7
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
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    gate = view.gates[0]

    assert gate.is_open
    assert gate not in view.walls


def test_switch_does_not_block_player(window: arcade.Window) -> None:
    """Verifie qu'un interrupteur n'est pas un mur pour le joueur"""
    game_map = load_map_from_string(
        """
        width: 5
        height: 5
        switches:
          - id: first
            x: 2
            y: 2
        ---
        xxxxx
        x   x
        x ^ x
        x P x
        xxxxx
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    switch = view.switches[0]

    view.player.center_x = switch.center_x
    view.player.center_y = switch.center_y
    view.do_on_update(1 / 60)

    assert switch not in view.walls
    assert window.current_view is view


def test_boomerang_returning_can_toggle_switch(window: arcade.Window) -> None:
    """Verifie que le boomerang active un interrupteur meme au retour"""
    game_map = load_map_from_string(
        """
        width: 7
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
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    switch = view.switches[0]
    gate = view.gates[0]

    view.boomerang.center_x = switch.center_x
    view.boomerang.center_y = switch.center_y
    view.boomerang.state = BoomerangState.RETURNING
    view.boomerang.visible = True
    view.boomerang.active = True
    view.do_on_update(1 / 60)

    assert switch.is_on
    assert gate.is_open
    assert gate not in view.walls
    assert view.boomerang.state == BoomerangState.RETURNING


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
