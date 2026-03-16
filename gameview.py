from math import sqrt
from typing import Final
import arcade
from pyglet.graphics import Batch
from constants import *
from textures import *
from player import Player

from map import (
    Map,
    GridCell,
    compute_horizontal_spinner_limits,
    compute_vertical_spinner_limits,
)

# Transforme une coordonnée de grille en coordonnée pixel
def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


class SpinnerSprite(arcade.TextureAnimationSprite):
    is_horizontal: bool
    min_pos: int
    max_pos: int


class GameView(arcade.View):
    grounds: Final[arcade.SpriteList[arcade.Sprite]]
    walls: Final[arcade.SpriteList[arcade.Sprite]]
    crystals: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    spinners: Final[arcade.SpriteList[SpinnerSprite]]
    player_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    holes: Final[arcade.SpriteList[arcade.Sprite]]
    physics_engine: Final[arcade.PhysicsEngineSimple]
    camera: Final[arcade.camera.Camera2D]
    camera_score: Final[arcade.camera.Camera2D]
    world_width: Final[int]
    world_height: Final[int]

    player: Final[Player]

    def __init__(self, map: Map) -> None:
        super().__init__()

        self.map = map
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        self.grounds = arcade.SpriteList(use_spatial_hash=True)
        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.crystals = arcade.SpriteList(use_spatial_hash=True)
        self.spinners = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.camera = arcade.camera.Camera2D()
        self.camera_score = arcade.camera.Camera2D()
        self.crystal_sound = arcade.load_sound(":resources:sounds/coin5.wav")
        self.world_width = map.width * TILE_SIZE
        self.world_height = map.height * TILE_SIZE
        self.holes = arcade.SpriteList()


        for x in range(map.width):
            for y in range(map.height):

                grass = arcade.Sprite(
                    TEXTURE_GRASS,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                self.grounds.append(grass)

                cell = map.get(x, y)

                if cell == GridCell.BUSH:
                    bush = arcade.Sprite(
                        TEXTURE_BUSH,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.walls.append(bush)

                elif cell == GridCell.CRYSTAL:
                    crystal = arcade.TextureAnimationSprite(
                        animation=CRYSTALS,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.crystals.append(crystal)

                elif cell == GridCell.SPINNER_HORIZONTAL:
                    spinner = SpinnerSprite(
                        animation=ANIMATION_SPINNER,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )

                    spinner.is_horizontal = True

                    left_x, right_x = compute_horizontal_spinner_limits(map, x, y)

                    spinner.min_pos = grid_to_pixels(left_x)
                    spinner.max_pos = grid_to_pixels(right_x)

                    spinner.change_x = 3
                    spinner.change_y = 0

                    self.spinners.append(spinner)

                elif cell == GridCell.SPINNER_VERTICAL:
                    spinner = SpinnerSprite(
                        animation=ANIMATION_SPINNER,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )

                    spinner.is_horizontal = False

                    bottom_y, top_y = compute_vertical_spinner_limits(map, x, y)

                    spinner.min_pos = grid_to_pixels(bottom_y)
                    spinner.max_pos = grid_to_pixels(top_y)

                    spinner.change_x = 0
                    spinner.change_y = 3

                    self.spinners.append(spinner)

                elif cell == GridCell.HOLE:
                    hole = arcade.Sprite(
                    TEXTURE_HOLE,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                    self.holes.append(hole)

        self.player = Player (
            grid_to_pixels(map.player_start_x),
            grid_to_pixels(map.player_start_y),
        )
        self.player_list.append(self.player)

        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)

        self.score_batch = Batch()

        self.score_text = arcade.Text(
            text=f"{self.player.score}",
            x=20,
            y=self.window.height - 40,
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.score_batch
        )

    def on_show_view(self) -> None:
        self.window.width = min(MAX_WINDOW_WIDTH, self.world_width)
        self.window.height = min(MAX_WINDOW_HEIGHT, self.world_height)

    def on_draw(self) -> None:
        self.clear()

        with self.camera.activate():
            self.grounds.draw()
            self.walls.draw()
            self.crystals.draw()
            self.spinners.draw()
            self.player_list.draw()
        with self.camera_score.activate():
            self.score_batch.draw()

    def on_update(self, delta_time: float) -> None:
        self.physics_engine.update()

        self.player.update_animation()
        self.crystals.update_animation()
        self.spinners.update_animation()

        for spinner in self.spinners:
            spinner.center_x += spinner.change_x
            spinner.center_y += spinner.change_y

            if spinner.is_horizontal:
                if spinner.center_x >= spinner.max_pos:
                    spinner.center_x = spinner.max_pos
                    spinner.change_x = -3
                elif spinner.center_x <= spinner.min_pos:
                    spinner.center_x = spinner.min_pos
                    spinner.change_x = 3
            else:
                if spinner.center_y >= spinner.max_pos:
                    spinner.center_y = spinner.max_pos
                    spinner.change_y = -3
                elif spinner.center_y <= spinner.min_pos:
                    spinner.center_y = spinner.min_pos
                    spinner.change_y = 3

        camera_x = self.player.center_x
        if self.player.center_x < self.window.width / 2:
            camera_x = self.window.width / 2
        elif self.player.center_x > self.world_width - self.window.width / 2:
            camera_x = self.world_width - self.window.width / 2

        camera_y = self.player.center_y
        if self.player.center_y < self.window.height / 2:
            camera_y = self.window.height / 2
        elif self.player.center_y > self.world_height - self.window.height / 2:
            camera_y = self.world_height - self.window.height / 2

        self.camera.position = (camera_x, camera_y)


        collision_crystals = arcade.check_for_collision_with_list(self.player, self.crystals)
        for crystal in collision_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(self.crystal_sound)
            self.player.score += 1
            self.score_text.text = f"{self.player.score}"

        collision_spinners = arcade.check_for_collision_with_list(self.player, self.spinners)
        if collision_spinners:
            new_game_view = GameView(self.map)
            self.window.show_view(new_game_view)

        for hole in self.holes:
            if (sqrt((self.player.center_x - hole.center_x)**2 + (self.player.center_y - hole.center_y)**2)) <= 16:
                new_game_view = GameView(self.map)
                self.window.show_view(new_game_view)




    def on_key_press(self, symbol: int, modifiers: int) -> None:
        match symbol:

            case arcade.key.UP:
                self.player.up_pressed = True
            case arcade.key.DOWN:
                self.player.down_pressed = True
            case arcade.key.LEFT:
                self.player.left_pressed = True
            case arcade.key.RIGHT:
                self.player.right_pressed = True
            case arcade.key.ESCAPE:
                new_game_view = GameView(self.map)
                self.window.show_view(new_game_view)
        self.player.player_move()



    def on_key_release(self, symbol: int, modifiers: int) -> None:
        match symbol:
            case arcade.key.UP:
                self.player.up_pressed = False
            case arcade.key.DOWN:
                self.player.down_pressed = False
            case arcade.key.LEFT:
                self.player.left_pressed = False
            case arcade.key.RIGHT:
                self.player.right_pressed = False
        self.player.player_move()
