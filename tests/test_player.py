# --- test_player_camera.py ---
import arcade

from constants import PLAYER_MOVEMENT_SPEED, TILE_SIZE
from gameview import GameView
from map import load_map_from_string
from player import Direction


def make_open_view(window: arcade.Window) -> GameView:
    game_map = load_map_from_string(
        """
        width: 30
        height: 20
        ---
        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x                            x
        x P                          x
        x                            x
        xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        ---
        """
    )
    view = GameView(game_map)
    window.show_view(view)
    return view


def test_keyboard_keeps_moving_left_when_right_is_released(
    window: arcade.Window,
) -> None:
    """Verifie que relacher droite ne stoppe pas gauche si gauche est encore appuyee"""
    view = make_open_view(window)

    view.on_key_press(arcade.key.RIGHT, 0)
    view.on_key_press(arcade.key.LEFT, 0)
    view.on_key_release(arcade.key.RIGHT, 0)

    assert view.player.change_x == -PLAYER_MOVEMENT_SPEED


def test_player_direction_priority_matches_project_rules(
    window: arcade.Window,
) -> None:
    """Verifie la priorite des directions quand plusieurs touches sont appuyees"""
    view = make_open_view(window)

    view.on_key_press(arcade.key.RIGHT, 0)
    assert view.player.direction == Direction.EAST

    view.on_key_press(arcade.key.LEFT, 0)
    assert view.player.direction == Direction.WEST

    view.on_key_press(arcade.key.UP, 0)
    assert view.player.direction == Direction.NORTH

    view.on_key_press(arcade.key.DOWN, 0)
    assert view.player.direction == Direction.SOUTH


def test_escape_restarts_the_view(window: arcade.Window) -> None:
    """Verifie que la touche Escape remplace la vue courante par une nouvelle partie"""
    view = make_open_view(window)

    view.on_key_press(arcade.key.ESCAPE, 0)

    assert window.current_view is not view


def test_camera_is_clamped_inside_world(window: arcade.Window) -> None:
    """Verifie que la camera reste dans les limites du monde"""
    view = make_open_view(window)

    view.player.center_x = TILE_SIZE
    view.player.center_y = TILE_SIZE
    view.do_on_update(1 / 60)
    assert view.camera.position == (window.width / 2, window.height / 2)

    view.player.center_x = view.world_width - TILE_SIZE
    view.player.center_y = view.world_height - TILE_SIZE
    view.do_on_update(1 / 60)
    assert view.camera.position == (
        view.world_width - window.width / 2,
        view.world_height - window.height / 2,
    )
