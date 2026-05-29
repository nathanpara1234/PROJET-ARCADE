import random
from math import sqrt
import arcade
import networkx as nx
from gameview import GameView
from map import load_map_from_string
from weapons import BoomerangState
from enemies import Bat, Blob, SpinnerSprite
from world_builder import compute_horizontal_spinner_limits, compute_vertical_spinner_limits
from constants import TILE_SIZE, BAT_MOUVEMENT_SPEED, MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT

MAP_TEXT = """width: 15
height: 10
---
xxxxxxxxxxxxxxx
x             x
x             x
x             x
x      v      x
x             x
x             x
x             x
x      P      x
xxxxxxxxxxxxxxx
---"""

BAT_START_X = 7 * TILE_SIZE + TILE_SIZE // 2
BAT_START_Y = 5 * TILE_SIZE + TILE_SIZE // 2


def test_valid_pos_inside_field() -> None:
    """valid_pos retourne True pour toute position dans le champ d'action."""
    bat = Bat(start_x=BAT_START_X, start_y=BAT_START_Y, world_width=MAX_WINDOW_WIDTH, world_height=MAX_WINDOW_HEIGHT)
    assert bat.valid_pos(BAT_START_X, BAT_START_Y)
    assert bat.valid_pos(BAT_START_X + 50, BAT_START_Y)
    assert bat.valid_pos(BAT_START_X, BAT_START_Y - 50)
    assert bat.valid_pos(BAT_START_X - 99, BAT_START_Y + 99)


def test_valid_pos_outside_field() -> None:
    """valid_pos retourne False pour une position hors du champ d'action."""
    bat = Bat(start_x=BAT_START_X, start_y=BAT_START_Y, world_width=MAX_WINDOW_WIDTH, world_height=MAX_WINDOW_HEIGHT)
    assert not bat.valid_pos(BAT_START_X + 100, BAT_START_Y)
    assert not bat.valid_pos(BAT_START_X - 100, BAT_START_Y)
    assert not bat.valid_pos(BAT_START_X, BAT_START_Y + 100)
    assert not bat.valid_pos(BAT_START_X, BAT_START_Y - 100)


def test_bat_stays_in_action_field() -> None:
    """La chauve-souris ne sort jamais de son champ d'action sur 600 frames."""
    random.seed(42)
    bat = Bat(
        start_x=BAT_START_X,
        start_y=BAT_START_Y,
        world_width=MAX_WINDOW_WIDTH,
        world_height=MAX_WINDOW_HEIGHT,
    )

    for i in range(600):
        bat.move(nx.Graph(), None)
        assert abs(bat.center_x - BAT_START_X) < 100
        assert abs(bat.center_y - BAT_START_Y) < 100


def test_bat_moves_at_constant_speed() -> None:
    """Quand la chauve-souris avance, elle parcourt exactement BAT_MOVEMENT_SPEED pixels"""
    random.seed(42)
    bat = Bat(
        start_x=BAT_START_X,
        start_y=BAT_START_Y,
        world_width=MAX_WINDOW_WIDTH,
        world_height=MAX_WINDOW_HEIGHT,
    )

    x_before, y_before = bat.center_x, bat.center_y
    bat.move(nx.Graph(), None)
    dx = bat.center_x - x_before
    dy = bat.center_y - y_before

    assert dx != 0 or dy != 0
    distance = sqrt(dx**2 + dy**2)
    assert abs(distance - BAT_MOUVEMENT_SPEED) < 0.01



def test_bat_count_on_map(window: arcade.Window) -> None:
    """La map de test contient exactement une chauve-souris"""
    game_map = load_map_from_string(MAP_TEXT)
    view = GameView(game_map)
    window.show_view(view)

    assert len(view.world.enemies) == 1


def test_player_touching_bat_triggers_restart(window: arcade.Window) -> None:
    """Le joueur meurt quand il touche une chauve-souris : la vue est remplacée"""
    game_map = load_map_from_string(MAP_TEXT)
    view = GameView(game_map)
    window.show_view(view)

    bat = view.world.enemies[0]
    view.player.center_x = bat.center_x
    view.player.center_y = bat.center_y

    view.do_on_update(1 / 60)

    assert window.current_view is not view


def test_bat_killed_by_boomerang(window: arcade.Window) -> None:
    """La chauve-souris est retirée du jeu quand le boomerang la touche"""
    game_map = load_map_from_string(MAP_TEXT)
    view = GameView(game_map)
    window.show_view(view)

    bat = view.world.enemies[0]

    view.boomerang.launch(view.player)
    view.boomerang.center_x = bat.center_x
    view.boomerang.center_y = bat.center_y
    view.boomerang.change_x = 1
    view.boomerang.change_y = 0

    initial_count = len(view.world.enemies)
    view.do_on_update(1 / 60)
    assert len(view.world.enemies) == initial_count - 1


def test_bat_killed_by_sword(window: arcade.Window) -> None:
    """La chauve-souris est retirée du jeu quand l'épée la touche"""
    game_map = load_map_from_string(MAP_TEXT)
    view = GameView(game_map)
    window.show_view(view)

    bat = view.world.enemies[0]

    view.sword.active = True
    view.sword.visible = True

    view.sword.center_x = bat.center_x
    view.sword.center_y = bat.center_y

    initial_count = len(view.world.enemies)
    view.do_on_update(1 / 60)
    assert len(view.world.enemies) == initial_count - 1


MAP_TEXT_BLOB = """width: 15
height: 10
---
xxxxxxxxxxxxxxx
x             x
x             x
x             x
x      b      x
x             x
x             x
x             x
x      P      x
xxxxxxxxxxxxxxx
---"""

BLOB_START_X = 7 * TILE_SIZE + TILE_SIZE // 2
BLOB_START_Y = 5 * TILE_SIZE + TILE_SIZE // 2


def test_blob_initial_state() -> None:
    """Un blob démarre avec un chemin vide et un index à 0"""
    blob = Blob(start_x=BLOB_START_X, start_y=BLOB_START_Y, world_width=MAX_WINDOW_WIDTH, world_height=MAX_WINDOW_HEIGHT)
    assert blob.path == []
    assert blob.i == 0


def test_blob_count_on_map(window: arcade.Window) -> None:
    """La map de test contient exactement un blob"""
    game_map = load_map_from_string(MAP_TEXT_BLOB)
    view = GameView(game_map)
    window.show_view(view)

    assert len(view.world.enemies) == 1

def test_player_touching_blob_triggers_restart(window: arcade.Window) -> None:
    """Le joueur meurt quand il touche un blob : la vue est remplacée"""
    game_map = load_map_from_string(MAP_TEXT_BLOB)
    view = GameView(game_map)
    window.show_view(view)

    blob = view.world.enemies[0]
    view.player.center_x = blob.center_x
    view.player.center_y = blob.center_y

    view.do_on_update(1 / 60)

    assert window.current_view is not view


def test_blob_killed_by_boomerang(window: arcade.Window) -> None:
    """Le blob est retiré du jeu quand le boomerang le touche"""
    game_map = load_map_from_string(MAP_TEXT_BLOB)
    view = GameView(game_map)
    window.show_view(view)

    blob = view.world.enemies[0]

    view.boomerang.launch(view.player)
    view.boomerang.center_x = blob.center_x
    view.boomerang.center_y = blob.center_y
    view.boomerang.change_x = 1
    view.boomerang.change_y = 0

    initial_count = len(view.world.enemies)
    view.do_on_update(1 / 60)
    assert len(view.world.enemies) == initial_count - 1


def test_blob_killed_by_sword(window: arcade.Window) -> None:
    """Le blob est retiré du jeu quand l'épee le touche"""
    game_map = load_map_from_string(MAP_TEXT_BLOB)
    view = GameView(game_map)
    window.show_view(view)

    blob = view.world.enemies[0]

    view.sword.active = True
    view.sword.visible = True

    view.sword.center_x = blob.center_x
    view.sword.center_y = blob.center_y

    initial_count = len(view.world.enemies)
    view.do_on_update(1 / 60)
    assert len(view.world.enemies) == initial_count - 1


def test_blob_chases_player_when_visible(window: arcade.Window) -> None:
    """Le blob se rapproche du joueur quand il entre dans sa ligne de vue"""
    game_map = load_map_from_string(MAP_TEXT_BLOB)
    view = GameView(game_map)
    window.show_view(view)

    blob = view.world.enemies[0]

    view.player.center_x = blob.center_x
    view.player.center_y = blob.center_y + 3 * TILE_SIZE

    distance_before = sqrt(
        (blob.center_x - view.player.center_x) ** 2
        + (blob.center_y - view.player.center_y) ** 2
    )
    window.test(10)
    distance_after = sqrt(
        (blob.center_x - view.player.center_x) ** 2
        + (blob.center_y - view.player.center_y) ** 2
    )

    assert distance_after < distance_before


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
    blob = view.world.enemies[0]
    gate = view.interactions.gates[0]

    assert not gate.is_open
    assert gate in view.world.walls
    assert not arcade.has_line_of_sight(blob.position, view.player.position, view.world.walls)


def test_blob_does_not_see_player_behind_bush_wall(window: arcade.Window) -> None:
    """Un buisson entre le blob et le joueur bloque sa ligne de vue"""
    game_map = load_map_from_string(
"""width: 9
height: 5
---
xxxxxxxxx
x       x
x b x P x
x       x
xxxxxxxxx
---"""
    )
    view = GameView(game_map)
    window.show_view(view)

    blob = view.world.enemies[0]

    assert not arcade.has_line_of_sight(blob.position, view.player.position, view.world.walls)


MAP_TEXT_SPINNER = """width: 7
height: 5
---
xxxxxxx
x     x
x  s  x
x P   x
xxxxxxx
---"""


def test_spinner_moves_horizontally(window: arcade.Window) -> None:
    """le spinner doit avancer sur x et pas bouger sur y"""
    spinner = SpinnerSprite(center_x=100, center_y=100, is_horizontal=True, min_pos=50, max_pos=200)
    initial_x = spinner.center_x
    spinner.spinner_move()
    assert spinner.center_x != initial_x
    assert spinner.center_y == 100  # y ne doit pas changer


def test_blob_random_axis_in_bounds() -> None:
    """Verifie que random_axis donne une valeur dans la zone"""
    import random
    for i in range(5):
        val = Blob.random_axis(start=100, limit=50, world_max=500)
        assert 50 <= val <= 150


def test_spinner_fait_demi_tour_au_max(window: arcade.Window) -> None:
    """quand le spinner atteint sa limite haute il doit faire demi-tour"""
    spinner = SpinnerSprite(center_x=100, center_y=100, is_horizontal=True, min_pos=50, max_pos=150)
    new_pos, new_speed = spinner.bounce(150, 5)
    assert new_pos == 150
    assert new_speed < 0


def test_spinner_fait_demi_tour_au_min(window: arcade.Window) -> None:
    """quand le spinner atteint sa limite basse il repart dans l'autre sens"""
    spinner = SpinnerSprite(center_x=80, center_y=80, is_horizontal=False, min_pos=50, max_pos=150)
    new_pos, new_speed = spinner.bounce(50, 0)
    assert new_pos == 50
    assert new_speed > 0


def test_closest_node() -> None:
    """Verifie que closest_node trouve le bon noeud"""
    G = nx.Graph()
    G.add_node((0, 0))
    G.add_node((10, 10))
    G.add_node((100, 100))
    assert Blob.closest_node(G, 8, 9) == (10, 10)
    assert Blob.closest_node(G, 1, 1) == (0, 0)


def test_horizontal_spinner_limits_stop_before_bushes() -> None:
    """Verifie les limites gauche/droite d'un spinner horizontal"""
    game_map = load_map_from_string(MAP_TEXT_SPINNER)
    left_x, right_x = compute_horizontal_spinner_limits(game_map, 2, 2)

    assert left_x == 1
    assert right_x == 5


def test_vertical_spinner_limits_stop_before_bushes() -> None:
    """Verifie les limites bas/haut d'un spinner vertical"""
    text = """width: 5
height: 7
---
xxxxx
x   x
x S x
x   x
x P x
x   x
xxxxx
---"""
    game_map = load_map_from_string(text)
    bottom_y, top_y = compute_vertical_spinner_limits(game_map, 2, 4)

    assert bottom_y == 1
    assert top_y == 5


def test_player_touching_spinner_triggers_restart(window: arcade.Window) -> None:
    """Le joueur meurt quand il touche un spinner"""
    game_map = load_map_from_string(MAP_TEXT_SPINNER)
    view = GameView(game_map)
    window.show_view(view)

    spinner = view.world.spinners[0]
    view.player.center_x = spinner.center_x
    view.player.center_y = spinner.center_y

    view.do_on_update(1 / 60)

    assert window.current_view is not view


def test_spinner_killed_by_boomerang(window: arcade.Window) -> None:
    """Le spinner est retire du jeu quand le boomerang le touche"""
    game_map = load_map_from_string(MAP_TEXT_SPINNER)
    view = GameView(game_map)
    window.show_view(view)

    spinner = view.world.spinners[0]
    view.boomerang.launch(view.player)
    view.boomerang.center_x = spinner.center_x
    view.boomerang.center_y = spinner.center_y
    view.boomerang.change_x = 1
    view.boomerang.change_y = 0

    initial_count = len(view.world.spinners)
    view.do_on_update(1 / 60)

    assert len(view.world.spinners) == initial_count - 1


def test_spinner_killed_by_sword(window: arcade.Window) -> None:
    """Le spinner est retire du jeu quand l'epee le touche"""
    game_map = load_map_from_string(MAP_TEXT_SPINNER)
    view = GameView(game_map)
    window.show_view(view)

    spinner = view.world.spinners[0]
    view.sword.active = True
    view.sword.visible = True

    view.sword.center_x = spinner.center_x
    view.sword.center_y = spinner.center_y

    initial_count = len(view.world.spinners)
    view.do_on_update(1 / 60)

    assert len(view.world.spinners) == initial_count - 1
