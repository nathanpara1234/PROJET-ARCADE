from typing import Final
import arcade

ORIG_TILE_SIZE = (16, 16)

def _load_grid(
    file: str,
    columns: int,
    rows: int,
    tile_size: tuple[int, int] = ORIG_TILE_SIZE
) -> list[arcade.Texture]:
    """
    Loads a texture grid from a spritesheet.

    Args:
        file:
            Path to the spritesheet file name.
        columns:
            The number of columns in the grid.
        rows:
            The number of rows in the grid.
        tile_size (optional):
            The size in pixels of one element of the grid. Defaults to the
            standard tile size of `(16, 16)` that we use in our assets.

    Returns:
        A list of the loaded textures, flattened by row. The texture at grid
        coordinates `(x, y)` is at index `(y * columns) + x` in the list.
    """
    spritesheet = arcade.load_spritesheet(file)
    return spritesheet.get_texture_grid(tile_size, columns, columns * rows)

_overworld_grid = _load_grid("assets/Top_Down_Adventure_Pack_v.1.0/Overworld_Tileset.png", 18, 13)

TEXTURE_GRASS: Final[arcade.Texture] = _overworld_grid[18*1 + 6]
TEXTURE_BUSH: Final[arcade.Texture] = _overworld_grid[18*3 + 5]

def _load_animation_strip(
    file: str,
    frame_count: int,
    frame_duration: int = 100,
    tile_size: tuple[int, int] = ORIG_TILE_SIZE,
) -> arcade.TextureAnimation:
    """
    Loads an animation strip from a line-oriented spritesheet.

    Args:
        file:
            Path to the spritesheet file name.
        frame_count:
            The number of frames in the animation, which should also be the
            number of sub-images in the file.
        frame_duration (optional):
            The duration of each frame in ms (defaults to 100).
        tile_size (optional):
            The size in pixels of one element of the grid, i.e.,  of a frame.
            Defaults to the standard tile size of `(16, 16)` that we use in our
            assets.

    Returns:
        An `arcade.TextureAnimation` representing the full animation.
    """
    grid = _load_grid(file, columns=frame_count, rows=1, tile_size=tile_size)
    keyframes = [arcade.TextureKeyframe(frame, frame_duration) for frame in grid]
    return arcade.TextureAnimation(keyframes)

ANIMATION_PLAYER_IDLE_DOWN: Final[arcade.TextureAnimation] = \
    _load_animation_strip("assets/Top_Down_Adventure_Pack_v.1.0/Char_Sprites/char_idle_down_anim_strip_6.png", 6)
CRYSTALS: Final[arcade.TextureAnimation] = \
    _load_animation_strip("assets/Top_Down_Adventure_Pack_v.1.0/Props_Items_(animated)/crystal_item_anim_strip_6.png", 6)

ANIMATION_SPINNER: Final[arcade.TextureAnimation] = \
    _load_animation_strip("assets/Top_Down_Adventure_Pack_v.1.0/Enemies_Sprites/Spinner_Sprites/spinner_run_attack_anim_all_dir_strip_8.png",3)
