import arcade


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
    while view.boomerang.state == BoomerangState.LAUNCHING:
        view.boomerang.update_boomerang(view.player, view.world.walls, view.world.all_enemies)

    assert view.boomerang.state == BoomerangState.RETURNING


def test_r_key_switches_active_weapon(window: arcade.Window) -> None:
    """Verifie que la touche R alterne entre boomerang et epee"""
    view = make_weapon_view(window)

    view.on_key_press(arcade.key.R, 0)
    assert view.active_weapon == WeaponType.SWORD

    view.on_key_press(arcade.key.R, 0)
    assert view.active_weapon == WeaponType.BOOMERANG


def test_sword_deactivates_after_duration(window: arcade.Window) -> None:
    """Verifie que l'epee se desactive apres sa duree d'attaque"""
    view = make_weapon_view(window)
    view.on_key_press(arcade.key.R, 0)  # passe en mode épée
    view.on_key_press(arcade.key.D, 0)  # attaque
    assert view.sword.active
    view.do_on_update(0.35)  # plus de 0.3s
    assert not view.sword.active


def test_boomerang_returns_after_hitting_wall(window: arcade.Window) -> None:
    """Verifie que le boomerang revient quand il touche un mur"""
    view = make_weapon_view(window)
    view.player.direction = Direction.WEST
    view.boomerang.launch(view.player)
    for i in range(100):
        view.boomerang.update_boomerang(view.player, view.world.walls, view.world.all_enemies)
        if view.boomerang.state == BoomerangState.RETURNING:
            break
    assert view.boomerang.state == BoomerangState.RETURNING


def test_boomerang_kills_enemy_on_return(window: arcade.Window) -> None:
    """Verifie que le boomerang tue un ennemi quand il revient vers le joueur"""
    game_map = load_map_from_string(
"""width: 10
height: 5
---
xxxxxxxxxx
x v      x
x        x
x P      x
xxxxxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)
    bat = view.world.enemies[0]
    view.boomerang.launch(view.player)
    view.boomerang.start_return()
    view.boomerang.center_x = bat.center_x
    view.boomerang.center_y = bat.center_y
    nb_avant = len(view.world.enemies)
    view.boomerang.update_boomerang(view.player, view.world.walls, view.world.all_enemies)
    assert len(view.world.enemies) == nb_avant - 1


def test_boomerang_comes_back_to_player(window: arcade.Window) -> None:
    """Le boomerang doit finir par revenir et disparaitre"""
    view = make_weapon_view(window)
    view.player.direction = Direction.EAST
    view.boomerang.launch(view.player)
    # on simule plein de frames pour laisser le temps au boomerang de revenir
    for i in range(200):
        view.boomerang.update_boomerang(view.player, view.world.walls, view.world.all_enemies)
        if view.boomerang.state == BoomerangState.INACTIVE:
            break
    assert view.boomerang.state == BoomerangState.INACTIVE


def test_boomerang_ignores_second_launch(window: arcade.Window) -> None:
    """Verifie qu'on ne peut pas relancer le boomerang pendant qu'il vole"""
    view = make_weapon_view(window)
    view.boomerang.launch(view.player)
    old_change_x = view.boomerang.change_x
    view.player.center_x += 100
    view.boomerang.launch(view.player)
    assert view.boomerang.change_x == old_change_x


def test_sword_ignores_second_attack(window: arcade.Window) -> None:
    """Verifie qu'une deuxieme frappe pendant une attaque en cours ne fait rien"""
    view = make_weapon_view(window)
    view.on_key_press(arcade.key.R, 0)
    view.on_key_press(arcade.key.D, 0)
    old_x = view.sword.center_x
    view.player.center_x += 200
    view.on_key_press(arcade.key.D, 0)
    assert view.sword.center_x == old_x


def test_sword_collects_crystal(window: arcade.Window) -> None:
    """Verifie que l'epee peut ramasser un cristal et augmenter le score"""
    view = make_weapon_view(window)
    view.active_weapon = WeaponType.SWORD
    crystal = view.world.crystals[0]
    view.player.center_x = crystal.center_x
    view.player.center_y = crystal.center_y
    view.player.direction = Direction.EAST

    view.on_key_press(arcade.key.D, 0)
    view.do_on_update(1 / 60)

    assert len(view.world.crystals) == 0
    assert view.player.score == 1
