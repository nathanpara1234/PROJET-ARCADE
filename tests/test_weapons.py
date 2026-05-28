import arcade

from constants import BOOMERANG_MAX_DISTANCE
from gameview import GameView
from map import load_map_from_string
from player import Direction
from weapons import BoomerangState, WeaponType


def make_weapon_view(window: arcade.Window) -> GameView:
    game_map = load_map_from_string(
"""width: 10
height: 5
---
xxxxxxxxxx
x        x
x   *    x
x P      x
xxxxxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    return view


def test_boomerang_launches_in_player_direction(window: arcade.Window) -> None:
    """Verifie que le boomerang part dans la direction regardee par le joueur"""
    view = make_weapon_view(window)
    view.player.direction = Direction.EAST

    view.on_key_press(arcade.key.D, 0)

    assert view.boomerang.state == BoomerangState.LAUNCHING
    assert view.boomerang.change_x > 0
    assert view.boomerang.change_y == 0


def test_boomerang_starts_returning_after_max_distance(
    window: arcade.Window,
) -> None:
    """Verifie que le boomerang revient apres avoir atteint sa distance maximale"""
    view = make_weapon_view(window)
    view.player.direction = Direction.EAST
    view.boomerang.launch(view.player)
    view.boomerang.travelled_distance = BOOMERANG_MAX_DISTANCE

    view.boomerang.update_boomerang(view.player, view.walls, view.all_enemies)

    assert view.boomerang.state == BoomerangState.RETURNING


def test_r_key_switches_active_weapon(window: arcade.Window) -> None:
    """Verifie que la touche R alterne entre boomerang et epee"""
    view = make_weapon_view(window)

    view.on_key_press(arcade.key.R, 0)
    assert view.active_weapon == WeaponType.SWORD

    view.on_key_press(arcade.key.R, 0)
    assert view.active_weapon == WeaponType.BOOMERANG


def test_sword_collects_crystal(window: arcade.Window) -> None:
    """Verifie que l'epee peut ramasser un cristal et augmenter le score"""
    view = make_weapon_view(window)
    view.active_weapon = WeaponType.SWORD
    crystal = view.crystals[0]
    view.player.center_x = crystal.center_x
    view.player.center_y = crystal.center_y
    view.player.direction = Direction.EAST

    view.on_key_press(arcade.key.D, 0)
    view.do_on_update(1 / 60)

    assert len(view.crystals) == 0
    assert view.player.score == 1
