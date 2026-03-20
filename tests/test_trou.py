# TEST 1 : TROU SEPARER (DOIT MARCHER)
import arcade  
from gameview import GameView
from map import Map

from textwrap import dedent

from map import load_map_from_string, GridCell


def test_holes_separated() -> None:
    text = dedent("""\
        width: 7
        height: 5
        ---
        xxxxxxx
        x     x
        x O O x
        x     x
        xxxxxxx
        ---
    """)

    game_map = load_map_from_string(text)

    assert game_map.get(2, 2) == GridCell.HOLE
    assert game_map.get(4, 2) == GridCell.HOLE




# TEST 2 : TROU COLLE (DOIT TUER)

def test_holes_adjacent() -> None:
    text = dedent("""\
        width: 7
        height: 5
        ---
        xxxxxxx
        x     x
        x OO  x
        x     x
        xxxxxxx
        ---
    """)

    game_map = load_map_from_string(text)

    assert game_map.get(2, 2) == GridCell.HOLE
    assert game_map.get(3, 2) == GridCell.HOLE
