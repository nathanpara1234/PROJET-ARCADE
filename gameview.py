from typing import Final
import arcade  # ty: ignore[unresolved-import]

from constants import *
from textures import *
from map import (
    Map,
    GridCell,
    compute_horizontal_spinner_limits,
    compute_vertical_spinner_limits,
)


# Transforme une coordonnée de grille en coordonnée pixel
# Le sprite est placé au centre de la case
def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


class GameView(arcade.View):
    grounds: Final[arcade.SpriteList[arcade.Sprite]]
    walls: Final[arcade.SpriteList[arcade.Sprite]]
    crystals: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    spinners: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    player_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]

    physics_engine: Final[arcade.PhysicsEngineSimple]
    camera: Final[arcade.camera.Camera2D]

    world_width: Final[int]
    world_height: Final[int]

    player: Final[arcade.TextureAnimationSprite]

    def __init__(self, map: Map) -> None:
        # Initialisation obligatoire de la vue Arcade
        super().__init__()

        # On garde la map actuelle pour pouvoir reset la même partie
        self.map = map

        # Couleur de fond
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        # Sprite lists
        self.grounds = arcade.SpriteList(use_spatial_hash=True)
        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.crystals = arcade.SpriteList(use_spatial_hash=True)

        # Les spinners bougent, donc pas de spatial hash ici
        self.spinners = arcade.SpriteList()

        self.player_list = arcade.SpriteList()

        # Caméra
        self.camera = arcade.camera.Camera2D()

        # Son ramassage cristal
        self.crystal_sound = arcade.load_sound(":resources:sounds/coin5.wav")

        # Taille du monde à partir de la map
        self.world_width = map.width * TILE_SIZE
        self.world_height = map.height * TILE_SIZE

        # Construction du monde à partir de la map
        for x in range(map.width):
            for y in range(map.height):
                # Il y a toujours de l'herbe sur chaque case
                grass = arcade.Sprite(
                    TEXTURE_GRASS,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                self.grounds.append(grass)

                cell = map.get(x, y)

                # Buisson
                if cell == GridCell.BUSH:
                    bush = arcade.Sprite(
                        TEXTURE_BUSH,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.walls.append(bush)

                # Cristal
                elif cell == GridCell.CRYSTAL:
                    crystal = arcade.TextureAnimationSprite(
                        animation=CRYSTALS,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.crystals.append(crystal)

                # Spinner horizontal
                elif cell == GridCell.SPINNER_HORIZONTAL:
                    spinner = arcade.TextureAnimationSprite(
                        animation=ANIMATION_SPINNER,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )

                    # On stocke orientation et limites directement sur le sprite
                    spinner.is_horizontal = True

                    left_x, right_x = compute_horizontal_spinner_limits(map, x, y)

                    # Limites en pixels
                    spinner.min_pos = grid_to_pixels(left_x)
                    spinner.max_pos = grid_to_pixels(right_x)

                    # Direction initiale : vers la droite
                    spinner.change_x = 3
                    spinner.change_y = 0

                    self.spinners.append(spinner)

                # Spinner vertical
                elif cell == GridCell.SPINNER_VERTICAL:
                    spinner = arcade.TextureAnimationSprite(
                        animation=ANIMATION_SPINNER,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )

                    spinner.is_horizontal = False

                    bottom_y, top_y = compute_vertical_spinner_limits(map, x, y)

                    # Limites en pixels
                    spinner.min_pos = grid_to_pixels(bottom_y)
                    spinner.max_pos = grid_to_pixels(top_y)

                    # Direction initiale : vers le haut
                    spinner.change_x = 0
                    spinner.change_y = 3

                    self.spinners.append(spinner)

        # Création du joueur à partir de la map
        self.player = arcade.TextureAnimationSprite(
            animation=ANIMATION_PLAYER_IDLE_DOWN,
            scale=SCALE,
            center_x=grid_to_pixels(map.player_start_x),
            center_y=grid_to_pixels(map.player_start_y),
        )
        self.player_list.append(self.player)

        # Physique du joueur contre les murs
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)

    def on_show_view(self) -> None:
        """Called automatically by 'window.show_view(game_view)' in main.py."""
        self.window.width = min(MAX_WINDOW_WIDTH, self.world_width)
        self.window.height = min(MAX_WINDOW_HEIGHT, self.world_height)

    def on_draw(self) -> None:
        """Render the screen."""
        self.clear()

        with self.camera.activate():
            self.grounds.draw()
            self.walls.draw()
            self.crystals.draw()
            self.spinners.draw()
            self.player_list.draw()

    def on_update(self, delta_time: float) -> None:
        """Called once per frame, before drawing."""
        # Physique du joueur
        self.physics_engine.update()

        # Mise à jour animations
        self.player.update_animation()
        self.crystals.update_animation()
        self.spinners.update_animation()

        # Déplacement des spinners
        for spinner in self.spinners:
            spinner.center_x += spinner.change_x
            spinner.center_y += spinner.change_y

            # Spinner horizontal
            if spinner.is_horizontal:
                if spinner.center_x >= spinner.max_pos:
                    spinner.center_x = spinner.max_pos
                    spinner.change_x = -3
                elif spinner.center_x <= spinner.min_pos:
                    spinner.center_x = spinner.min_pos
                    spinner.change_x = 3

            # Spinner vertical
            else:
                if spinner.center_y >= spinner.max_pos:
                    spinner.center_y = spinner.max_pos
                    spinner.change_y = -3
                elif spinner.center_y <= spinner.min_pos:
                    spinner.center_y = spinner.min_pos
                    spinner.change_y = 3

        # Caméra limitée aux bords du monde
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

        # Ramassage des cristaux
        collision_crystals = arcade.check_for_collision_with_list(self.player, self.crystals)
        for crystal in collision_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(self.crystal_sound)

        # Collision joueur / spinner = reset immédiat
        collision_spinners = arcade.check_for_collision_with_list(self.player, self.spinners)
        if collision_spinners:
            new_game_view = GameView(self.map)
            self.window.show_view(new_game_view)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        """Called when the user presses a key on the keyboard."""
        match symbol:
            case arcade.key.RIGHT:
                self.player.change_x = +PLAYER_MOVEMENT_SPEED

            case arcade.key.LEFT:
                self.player.change_x = -PLAYER_MOVEMENT_SPEED

            case arcade.key.UP:
                self.player.change_y = +PLAYER_MOVEMENT_SPEED

            case arcade.key.DOWN:
                self.player.change_y = -PLAYER_MOVEMENT_SPEED

            case arcade.key.ESCAPE:
                # Reset avec la map actuelle
                new_game_view = GameView(self.map)
                self.window.show_view(new_game_view)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        """Called when the user releases a key on the keyboard."""
        # Meilleure gestion du clavier :
        # on n'arrête que le mouvement correspondant à la touche relâchée
        match symbol:
            case arcade.key.RIGHT:
                if self.player.change_x > 0:
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
