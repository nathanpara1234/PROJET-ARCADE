from textwrap import dedent

# On importe les fonctions que l'on veut tester
# load_map_from_string : transforme une string en Map
# compute_horizontal_spinner_limits : calcule les limites gauche/droite
# compute_vertical_spinner_limits : calcule les limites bas/haut
from map import (
    load_map_from_string,
    compute_horizontal_spinner_limits,
    compute_vertical_spinner_limits,
)


def test_horizontal_spinner_limits() -> None:# Imagination d'une petite map directement dans le test
    text = dedent("""\
        width: 7
        height: 5
        ---
        xxxxxxx
        x     x
        x  s  x
        x     x
        xxxxxxx
        ---
    """)
    game_map = load_map_from_string(text) # On convertit le string qu'on a créer en objet Map
    left_x, right_x = compute_horizontal_spinner_limits(game_map, 2, 2) #on place un spinner en (2,2) et on calcule ses limites de deplacements
    assert left_x == 1# Il doit pouvoir aller jusqu'au mur de gauche
    assert right_x == 5

# On crée une map avec un spinner vertical
def test_vertical_spinner_limits() -> None:
    text = dedent("""\
        width: 5
        height: 7
        ---
        xxxxx
        x   x
        x S x
        x   x
        x   x
        x   x
        xxxxx
        ---
    """)
    game_map = load_map_from_string(text)
    bottom_y, top_y = compute_vertical_spinner_limits(game_map, 2, 4) # le spinner vertical est situé en (2,4) et il doit pouvoir descendre jusqu'à la première case libre
    assert bottom_y == 1 # pouvoir descendre jusqu'à la première case libre
    assert top_y == 5# pouvoir monter jusqu'à la dernière case libre
