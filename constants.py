from typing import Final


WINDOW_TITLE: Final = "Adventure"
"""Title of the main window."""

SCALE: Final = 2.0
"""The global scale for all textures."""

TILE_SIZE: Final = 32
"""After scaling, the size of a tile."""

MAX_WINDOW_WIDTH: Final = 14 * TILE_SIZE
MAX_WINDOW_HEIGHT: Final = 14 * TILE_SIZE

PLAYER_MOVEMENT_SPEED: Final = 4

BLOB_MOUVEMENT_SPEED: Final = 1

SPINNER_SPEED: Final = 3
BOOMERANG_SPEED: Final = 8
BOOMERANG_MAX_DISTANCE: Final = 8 * TILE_SIZE

NAVMESH_DENSITY: int = 3

DRAW_NAVMESHES: Final = True

INDESTRUCTIBILITY_DURATION: Final = 10000
SPIKES_SWITCH_TIME: Final = 3.0

BAT_MOUVEMENT_SPEED: Final = 2
BAT_FRAQUENCY_MODIF_DIRECTION: Final = 2
BAT_ZONE_WIDTH: Final = 100

BLOB_ZONE_WIDTH: Final = 5 * TILE_SIZE
