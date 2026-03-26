from math import sqrt
from typing import Final
import arcade
from pyglet.graphics import Batch
from bat import Bat
from constants import *
from textures import *
from player import Player
from boomerang import Boomerang
from enum import Enum
from sword import *

from map import (
    Map,
    GridCell,
    compute_horizontal_spinner_limits,
    compute_vertical_spinner_limits,
)

# Transforme une coordonnée de grille en coordonnée pixel.
# Exemple : la case (x=2) devient la position au centre de la 3e tuile.
def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


# Sprite spécial pour les ennemis "spinner"
# On lui ajoute :
# - un axe de déplacement (horizontal ou vertical)
# - une position min et max à ne pas dépasser
class SpinnerSprite(arcade.TextureAnimationSprite):
    is_horizontal: bool
    min_pos: int
    max_pos: int

# Enum pour savoir quelle arme est actuellement équipée
class WeaponType(Enum):
    BOOMERANG = 1
    SWORD = 2

# Vue principale du jeu
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
    boomerang_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    boomerang: Final[Boomerang]
    sword_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    sword: Final[Sword]
    active_weapon: WeaponType
    bats: Final[arcade.SpriteList[Bat]]

    player: Final[Player]

    def __init__(self, map: Map) -> None:
        super().__init__()

        self.map = map
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        # Listes de sprites organisées par type
        self.grounds = arcade.SpriteList(use_spatial_hash=True)
        self.walls = arcade.SpriteList(use_spatial_hash=True)
        self.crystals = arcade.SpriteList(use_spatial_hash=True)
        self.spinners = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        self.camera = arcade.camera.Camera2D()
        self.camera_score = arcade.camera.Camera2D()

        # Son joué lors de la récupération d’un cristal
        self.crystal_sound = arcade.load_sound(":resources:sounds/coin5.wav")

        # Dimensions du monde en pixels
        self.world_width = map.width * TILE_SIZE
        self.world_height = map.height * TILE_SIZE

        self.holes = arcade.SpriteList()
        self.bats = arcade.SpriteList()
        # Initialisation du boomerang
        self.boomerang_list = arcade.SpriteList()
        self.boomerang = Boomerang()
        self.boomerang_list.append(self.boomerang)

        # Initialisation future de l’épée
        self.sword_list = arcade.SpriteList()

        # Parcours de toutes les cases de la map pour y placer les bons sprites
        for x in range(map.width):
            for y in range(map.height):

                # Chaque case reçoit d’abord un sol
                grass = arcade.Sprite(
                    TEXTURE_GRASS,
                    scale=SCALE,
                    center_x=grid_to_pixels(x),
                    center_y=grid_to_pixels(y),
                )
                self.grounds.append(grass)

                cell = map.get(x, y)

                # Si la case contient un buisson, il devient un mur
                if cell == GridCell.BUSH:
                    bush = arcade.Sprite(
                        TEXTURE_BUSH,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.walls.append(bush)

                # Si la case contient un cristal, on crée un sprite animé
                elif cell == GridCell.CRYSTAL:
                    crystal = arcade.TextureAnimationSprite(
                        animation=ANIMATION_CRYSTALS,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.crystals.append(crystal)

                # Spinner horizontal : va de gauche à droite entre deux limites
                elif cell == GridCell.SPINNER_HORIZONTAL:
                    spinner = SpinnerSprite(
                        animation=ANIMATION_SPINNER,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )

                    spinner.is_horizontal = True

                    # Calcule les bornes du déplacement horizontal
                    left_x, right_x = compute_horizontal_spinner_limits(map, x, y)

                    spinner.min_pos = grid_to_pixels(left_x)
                    spinner.max_pos = grid_to_pixels(right_x)

                    spinner.change_x = 3
                    spinner.change_y = 0

                    self.spinners.append(spinner)

                # Spinner vertical : va de bas en haut entre deux limites
                elif cell == GridCell.SPINNER_VERTICAL:
                    spinner = SpinnerSprite(
                        animation=ANIMATION_SPINNER,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )

                    spinner.is_horizontal = False

                    # Calcule les bornes du déplacement vertical
                    bottom_y, top_y = compute_vertical_spinner_limits(map, x, y)

                    spinner.min_pos = grid_to_pixels(bottom_y)
                    spinner.max_pos = grid_to_pixels(top_y)

                    spinner.change_x = 0
                    spinner.change_y = 3

                    self.spinners.append(spinner)

                # Trou dans lequel le joueur peut tomber
                elif cell == GridCell.HOLE:
                    hole = arcade.Sprite(
                        TEXTURE_HOLE,
                        scale=SCALE,
                        center_x=grid_to_pixels(x),
                        center_y=grid_to_pixels(y),
                    )
                    self.holes.append(hole)

                elif cell == GridCell.BAT:
                    bat = Bat(
                        start_x=grid_to_pixels(x),
                        start_y=grid_to_pixels(y),
                    )
                    self.bats.append(bat)

        # Création du joueur à sa position de départ sur la map
        self.player = Player(
            grid_to_pixels(map.player_start_x),
            grid_to_pixels(map.player_start_y),
        )
        self.player_list.append(self.player)

        # Initialisation de l’épée
        self.sword_list = arcade.SpriteList()
        self.sword = Sword()
        self.sword_list.append(self.sword)

        # Arme équipée au début
        self.active_weapon = WeaponType.BOOMERANG

        # Moteur physique simple : le joueur est bloqué par les murs
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)

        # Batch pour afficher plusieurs textes de HUD efficacement
        self.score_batch = Batch()

        # Texte du score
        self.score_text = arcade.Text(
            text=f"{self.player.score}",
            x=20,
            y=self.window.height - 40,
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.score_batch
        )

        # Texte de l’arme actuellement équipée
        self.weapon_text = arcade.Text(
            text="Boomerang",
            x=20,
            y=self.window.height - 70,
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.score_batch
        )

    def on_show_view(self) -> None:
        # Ajuste la taille de la fenêtre à la taille du monde,
        # sans dépasser les dimensions maximales autorisées
        self.window.width = min(MAX_WINDOW_WIDTH, self.world_width)
        self.window.height = min(MAX_WINDOW_HEIGHT, self.world_height)

    def on_draw(self) -> None:
        # Efface l’écran puis dessine le monde et enfin le HUD
        self.clear()

        with self.camera.activate():
            self.grounds.draw()
            self.walls.draw()
            self.holes.draw()
            self.crystals.draw()
            self.spinners.draw()
            self.player_list.draw()
            self.player.update_animation()
            self.boomerang_list.draw()
            self.sword_list.draw()
            self.bats.draw()
        with self.camera_score.activate():
            self.score_batch.draw()

    def on_update(self, delta_time: float) -> None:
        # Met à jour la physique du joueur
        self.physics_engine.update()

        # Met à jour les animations
        self.player.update_animation()
        self.crystals.update_animation()
        self.spinners.update_animation()
        self.boomerang.update_animation()
        self.boomerang.update_boomerang(self.player, self.walls, self.spinners)
        self.sword.update_animation()
        self.sword.update_sword(
            delta_time,
            self.spinners,
            self.crystals,
            self.player,
            self.crystal_sound
        )
        for bat in self.bats:
            bat.bat_move()
            bat.update_animation()

        for spinner in self.spinners:
            spinner.center_x += spinner.change_x
            spinner.center_y += spinner.change_y

            if spinner.is_horizontal:
                # Le spinner inverse sa direction s’il atteint une borne
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

        # Déplacement automatique des spinners
          # Gestion de la caméra : elle suit le joueur
        # tout en restant dans les limites de la map
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

        # Détection de collision entre le joueur et les cristaux
        collision_crystals = arcade.check_for_collision_with_list(self.player, self.crystals)
        for crystal in collision_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(self.crystal_sound)
            self.player.score += 1
            self.score_text.text = f"{self.player.score}"

            # Remet le texte de l’arme (ici ce passage pourrait être simplifié)
            self.weapon_text = arcade.Text(
                text="Boomerang",
                x=20,
                y=self.window.height - 70,
                color=arcade.color.WHITE,
                font_size=18,
                batch=self.score_batch
            )

        # Si le joueur touche un spinner, la partie recommence
        collision_spinners = arcade.check_for_collision_with_list(self.player, self.spinners)
        if collision_spinners:
            new_game_view = GameView(self.map)
            self.window.show_view(new_game_view)

        collision_bats = arcade.check_for_collision_with_list(self.player, self.bats)
        if collision_bats:
            new_game_view = GameView(self.map)
            self.window.show_view(new_game_view)

        collision_boomerang_bat = arcade.check_for_collision_with_list(self.boomerang, self.bats)
        if collision_boomerang_bat:
                bat.remove_from_sprite_lists()

        collision_sword_bat = arcade.check_for_collision_with_list(self.sword, self.bats)
        if collision_sword_bat:
                bat.remove_from_sprite_lists()


        # Si le joueur est suffisamment proche du centre d’un trou, la partie recommence
        for hole in self.holes:
            if (sqrt((self.player.center_x - hole.center_x) ** 2 + (self.player.center_y - hole.center_y) ** 2)) <= 16:
                new_game_view = GameView(self.map)
                self.window.show_view(new_game_view)

        # Mise à jour du texte affichant l’arme en cours
        if self.active_weapon == WeaponType.BOOMERANG:
            self.weapon_text.text = "Boomerang"
        else:
            self.weapon_text.text = "Sword"

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
                # D : utilise l’arme active
            case arcade.key.D:
                if self.active_weapon == WeaponType.BOOMERANG:
                    self.boomerang.launch(self.player)
                else:
                    self.sword.attack(self.player)

            # R : change d’arme
            case arcade.key.R:
                if self.active_weapon == WeaponType.BOOMERANG:
                    self.active_weapon = WeaponType.SWORD
                else:
                    self.active_weapon = WeaponType.BOOMERANG

        # Recalcule le mouvement du joueur après une touche pressée
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
