import sys

import arcade  # ty:ignore[unresolved-import]

from constants import *
from gameview import GameView
from map import load_map_from_file, InvalidMapFileException


def main() -> None:
    # Si un argument est donné, on charge ce fichier
    # Sinon, on charge maps/map1.txt par défaut
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "maps/map1.txt"

    # Lecture de la map
    try:
        game_map = load_map_from_file(filename)

    except InvalidMapFileException as e:
        print("Erreur dans le fichier de map :")
        print(e)
        return


    # Création de la fenêtre
    window = arcade.Window(MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT, WINDOW_TITLE)

    # Création de la vue du jeu avec la map chargée
    view = GameView(game_map)
    window.show_view(view)


    # Lancement du jeu
    arcade.run()


if __name__ == "__main__":
    main()
