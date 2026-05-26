# Tests archivés : interrupteurs, portails, conditions de portail.
# Provient de : tests/test_map.py, tests/test_gameplay.py, tests/test_enemies.py
# Ce fichier n'est pas exécuté par pytest (pas de préfixe test_).

import pytest
import arcade

from switches_gates_archive import condition_is_true
from gameview import GameView
from map import load_map_from_string, GridCell, InvalidMapFileException
from weapons import BoomerangState


# ============================================================
# Depuis test_map.py : tests conditions de portail
# ============================================================

def test_gate_condition_is_evaluated_without_arcade() -> None:
    """Verifie une condition logique de portail sans utiliser Arcade"""
    condition = {
        "and": [
            {"switch_is_on": "first"},
            {"not": [{"switch_is_on": "second"}]},
        ]
    }

    assert condition_is_true(condition, {"first": True, "second": False})
    assert not condition_is_true(condition, {"first": True, "second": True})


def test_gate_condition_or_is_evaluated_without_arcade() -> None:
    """Verifie une condition or/not de portail sans utiliser Arcade"""
    condition = {
        "or": [
            {"not": [{"switch_is_on": "first"}]},
            {"switch_is_on": "second"},
        ]
    }

    assert condition_is_true(condition, {"first": False, "second": False})
    assert condition_is_true(condition, {"first": True, "second": True})
    assert not condition_is_true(condition, {"first": True, "second": False})


def test_map_loads_switch_and_gate_yaml() -> None:
    """Verifie que le YAML cree bien un interrupteur et un portail"""
    text = """
        width: 5
        height: 3
        switches:
          - id: first
            x: 1
            y: 1
            state: on
        gates:
          - x: 3
            y: 1
            open_if:
              switch_is_on: first
        ---
        xxxxx
        x^ |x
        xPxxx
        ---
    """

    game_map = load_map_from_string(text)

    assert game_map.get(1, 1) == GridCell.SWITCH
    assert game_map.get(3, 1) == GridCell.GATE
    assert game_map.switches[0].id == "first"
    assert game_map.switches[0].is_on
    assert game_map.gates[0].open_if == {"switch_is_on": "first"}


def test_switch_state_is_off_by_default() -> None:
    """Verifie qu'un interrupteur sans state commence sur off"""
    game_map = load_map_from_string(
        """
        width: 5
        height: 3
        switches:
          - id: first
            x: 1
            y: 1
        ---
        xxxxx
        x^  x
        xPxxx
        ---
        """
    )

    assert not game_map.switches[0].is_on


def test_two_switches_cannot_share_same_id() -> None:
    """Verifie que deux interrupteurs ne peuvent pas avoir le meme id"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
            """
            width: 7
            height: 3
            switches:
              - id: first
                x: 1
                y: 1
              - id: first
                x: 3
                y: 1
            ---
            xxxxxxx
            x^ ^  x
            xPxxxxx
            ---
            """
        )


def test_gate_with_unknown_switch_is_invalid() -> None:
    """Verifie qu'un portail ne peut pas dependre d'un switch inconnu"""
    text = """
        width: 5
        height: 3
        gates:
          - x: 3
            y: 1
            open_if:
              switch_is_on: missing
        ---
        xxxxx
        x  |x
        xxxxx
        ---
    """

    with pytest.raises(InvalidMapFileException):
        load_map_from_string(text)


def test_switch_yaml_must_match_switch_character() -> None:
    """Verifie qu'un switch YAML doit etre place sur un caractere ^"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
            """
            width: 5
            height: 3
            switches:
              - id: first
                x: 1
                y: 1
            ---
            xxxxx
            x   x
            xPxxx
            ---
            """
        )


def test_gate_character_needs_yaml_configuration() -> None:
    """Verifie qu'un caractere | doit avoir une configuration gate"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
            """
            width: 5
            height: 3
            ---
            xxxxx
            x | x
            xPxxx
            ---
            """
        )


def test_binary_gate_condition_must_have_two_children() -> None:
    """Verifie que and/or doivent contenir exactement deux sous-conditions"""
    with pytest.raises(InvalidMapFileException):
        load_map_from_string(
            """
            width: 5
            height: 3
            switches:
              - id: first
                x: 1
                y: 1
            gates:
              - x: 3
                y: 1
                open_if:
                  and:
                    - switch_is_on: first
            ---
            xxxxx
            x^ |x
            xPxxx
            ---
            """
        )


# ============================================================
# Depuis test_gameplay.py : tests interrupteurs/portails
# ============================================================

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


# ============================================================
# Depuis test_enemies.py : test portail comme mur pour le blob
# ============================================================

def test_blob_sees_closed_gate_as_wall(window: arcade.Window) -> None:
    """Un portail ferme bloque la ligne de vue du blob comme un mur"""
    game_map = load_map_from_string(
        """
        width: 9
        height: 5
        switches:
          - id: first
            x: 1
            y: 1
        gates:
          - x: 4
            y: 2
            open_if:
              switch_is_on: first
        ---
        xxxxxxxxx
        x       x
        x b | P x
        x^      x
        xxxxxxxxx
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    blob = view.enemies[0]
    gate = view.gates[0]

    assert not gate.is_open
    assert gate in view.walls
    assert not arcade.has_line_of_sight(blob.position, view.player.position, view.walls)
