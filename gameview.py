from typing import Final
import arcade

from constants import *
from textures import *
import dataclasses
def grid_to_pixels(i: int) -> int:
    return i*TILE_SIZE + (TILE_SIZE // 2)


class GameView(arcade.View):
    """Main in-game view."""
    grounds: Final[arcade.SpriteList[arcade.Sprite]]
    walls: Final[arcade.SpriteList[arcade.Sprite]]
    crystals: Final[arcade.SpriteList[arcade.Sprite]]
    physics_engine: Final[arcade.PhysicsEngineSimple]
    camera: Final[arcade.camera.Camera2D]
    world_width: Final[int]
    world_height: Final[int]
    player: Final[arcade.TextureAnimationSprite]
    player_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]


    def __init__(self) -> None:

        self.player = arcade.TextureAnimationSprite(
            animation=ANIMATION_PLAYER_IDLE_DOWN,
            scale=SCALE,center_x=grid_to_pixels(2), center_y=grid_to_pixels(2)
        )
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.grounds = arcade.SpriteList(use_spatial_hash=True)
        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.crystals = arcade.SpriteList(use_spatial_hash=True)
        self.camera = arcade.camera.Camera2D()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)
        self.crystal_sound = arcade.load_sound(":resources:sounds/coin5.wav")
        # Magical incantion: initialize the Arcade view
        super().__init__()

        # Choose a nice comfy background color
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        # Setup our game
        self.world_width = 40 * TILE_SIZE
        self.world_height = 20 * TILE_SIZE

        for x in range (40):
            for y in range(20):

                grass = arcade.Sprite(
                    TEXTURE_GRASS,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                self.grounds.append(grass)

                if ((x == 0) or (x == 39) or (y == 0) or (y == 19)):
                    bush = arcade.Sprite(
                        TEXTURE_BUSH,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                    )
                    self.walls.append(bush)

        for (x, y) in [(3, 6), (7, 2), (2, 10), (3, 8)]:
            bush = arcade.Sprite (
                TEXTURE_BUSH,
                scale=SCALE,
                center_x=grid_to_pixels(x),
                center_y=grid_to_pixels(y),
            )
            self.walls.append(bush)
            self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)

        for (x,y) in [(5,2), (6,5), (3,5)]:
            crystals = arcade.TextureAnimationSprite (
                animation=CRYSTALS,
                scale=SCALE,
                center_x=grid_to_pixels(x),
                center_y=grid_to_pixels(y),
            )
            self.crystals.append(crystals)


    def on_show_view(self) -> None:
        """Called automatically by 'window.show_view(game_view)' in main.py."""
        # When we show the view, adjust the window's size to our world size.
        # If the world size is smaller than the maximum window size, we should
        # limit the size of the window.
        self.window.width = min(MAX_WINDOW_WIDTH, self.world_width)
        self.window.height = min(MAX_WINDOW_HEIGHT, self.world_height)

    def on_draw(self) -> None:
        """Render the screen."""
        self.clear() # always start with self.clear()

        self.grounds.draw()
        with self.camera.activate():
             self.grounds.draw()
             self.walls.draw()
             self.crystals.draw()
             self.player_list.draw()

    def on_update(self, delta_time: float) -> None:
        """Called once per frame, before drawing.

        This is where in-world time "advances", or "ticks".
        """
        self.physics_engine.update()
        self.player.update_animation()
        self.crystals.update_animation()
        #pour que la camera s'arrête sur le bord du jeu
        self.camera.position = self.player.position
        camera_x = self.player.center_x
        if ((self.player.center_x - self.window.width / 2) <0): # valeur<0, cela signifie que le bord gauche de la caméra serait en dehors de la limite gauche du jeu
            camera_x = self.window.width / 2 #position reste à la moitié de la largeur de la fenetre
        elif (self.player.center_x > self.world_width - self.window.width / 2 ):
            camera_x = self.world_width - self.window.width / 2

        camera_y = self.player.center_y
        if (self.player.center_y < self.window.height / 2):
            camera_y= self.window.height / 2
        elif (self.player.center_y > self.world_height -self.window.height / 2 ):
            camera_y = self.world_height -self.window.height / 2
        self.camera.position = (camera_x, camera_y)

        collision_crystals = arcade.check_for_collision_with_list(self.player, self.crystals)
        for crystal in collision_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(self.crystal_sound)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Called when the user presses a key on the keyboard."""
        match symbol:
            case arcade.key.RIGHT:
                # start moving to the right
                self.player.change_x = +PLAYER_MOVEMENT_SPEED
            case arcade.key.LEFT:
                # start moving to the left
                self.player.change_x = -PLAYER_MOVEMENT_SPEED
            case arcade.key.UP:
                # start moving upwards
                self.player.change_y = +PLAYER_MOVEMENT_SPEED
            case arcade.key.DOWN:
                # start moving downwards
                self.player.change_y = -PLAYER_MOVEMENT_SPEED
            case arcade.key.ESCAPE:
                new_game_view = GameView()
                self.window.show_view(new_game_view)



    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Called when the user releases a key on the keyboard."""
        match symbol:
            case arcade.key.RIGHT:        #le mouvement s'arrête seulement si le joueur se deplacé à droite.
                if self.player.change_x > 0:     #car si la droite est relacher et que le joueur va à gauche, il doit continuer sans s'arrêter
                    self.player.change_x = 0

            case arcade.key.LEFT:
                if self.player.change_x < 0:
                    self.player.change_x = 0

            case arcade.key.UP:
                if self.player.change_y > 0:
                    self.player.change_y = 0

            case arcade.key.DOWN:
                if self.player.change_y < 0:
                    self.player.change_y = 0
