from math import sqrt
import networkx as nx
from typing import Final
import arcade
from pyglet.graphics import Batch
from enemies import (
    Bat,
    SpinnerSprite,
    Blob,
    compute_horizontal_spinner_limits,
    compute_vertical_spinner_limits,
    )
from constants import *
from textures import *
from player import Player
from enum import Enum
from weapons import *

from map import (
    Map,
    GridCell,
)

# Transforme une coordonnée de grille en coordonnée pixel.
# Exemple : la case (x=2) devient la position au centre de la 3e tuile.
def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


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
    blobs: Final[arcade.SpriteList[Blob]]
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
        self.blobs = arcade.SpriteList()
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

                elif cell == GridCell.BLOB:
                    blob = Blob (
                    start_x=grid_to_pixels(x),
                    start_y=grid_to_pixels(y),
                    )
                    self.blobs.append(blob)

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

        self.weapon_text = arcade.Text(
            text="Arme : Boomerang", # Texte par défaut
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
            self.boomerang_list.draw()
            self.sword_list.draw()
            self.bats.draw()
            self.blobs.draw()
            '''if DRAW_NAVMESHES:
                the_navmesh = self.map.navmesh # On récupère ton graphe

            # 1. Dessin des points (nœuds) et des segments (arêtes)
            nodes = list(the_navmesh.nodes)
            for node in nodes:
                # Ton 'node' est déjà un tuple (x, y) en pixels
                arcade.draw_circle_filled(node[0], node[1], 2, arcade.color.BLACK)

                for neighbor in the_navmesh.neighbors(node):
                    # Dessine la ligne entre le point et son voisin
                    arcade.draw_line(node[0], node[1], neighbor[0], neighbor[1], arcade.color.BLACK, 2)

            # 2. Dessin du chemin rouge pour chaque Blob
            for slime in self.blobs:
                # On vérifie si l'ennemi a un chemin calculé
                if hasattr(slime, 'path') and slime.path:
                    # On s'assure qu'il y a au moins 2 points pour tracer une ligne
                    if len(slime.path) >= 2:
                        arcade.draw_line_strip(slime.path, arcade.color.RED, 2)'''
        with self.camera_score.activate():
            self.score_batch.draw()

    def restart_if_collision(self, enemies: arcade.SpriteList) -> None:
        # 1. Test des ennemis (chauve-souris, spinners)
        if arcade.check_for_collision_with_list(self.player, enemies):
            new_game_view = GameView(self.map)
            self.window.show_view(new_game_view)
            return # On s'arrête là si on a déjà touché un ennemi

        # 2. Test des trous
        for hole in self.holes:
            distance = sqrt((self.player.center_x - hole.center_x) ** 2 + (self.player.center_y - hole.center_y) ** 2)
            if distance <= 16:
                new_game_view = GameView(self.map)
                self.window.show_view(new_game_view)
                return

    def update_weapon_text(self) -> None:
        #"""Met à jour le texte de l'arme affiché à l'écran."""
        if self.active_weapon == WeaponType.BOOMERANG:
            self.weapon_text.text = "Arme : Boomerang"
        else:
            self.weapon_text.text = "Arme : Épée"

          # Gestion de la caméra : elle suit le joueur
        # tout en restant dans les limites de la map

    def update_camera_position(self) -> None :
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

    def on_update(self, delta_time: float) -> None:
        enemies = arcade.SpriteList()
        for bat in self.bats:
            enemies.append(bat)
        for blob in self.blobs:
            enemies.append(blob)
        for spinner in self.spinners:
            enemies.append(spinner)

        # Met à jour la physique du joueur
        self.physics_engine.update()
        # Met à jour les animations
        self.player.update_animation()
        self.player.player_move()
        self.update_camera_position()
        self.restart_if_collision(enemies)
        self.crystals.update_animation()
        self.spinners.update_animation()
        self.bats.update_animation()
        self.blobs.update_animation()
        self.boomerang.update_animation()
        self.boomerang.update_boomerang(self.player, self.walls, enemies)
        self.sword.update_animation()
        self.sword.update_sword(
            delta_time,
            enemies,
            self.crystals,
            self.player,
            self.crystal_sound
        )
        for bat in self.bats:
            bat.bat_move()
        for spinner in self.spinners:
            spinner.spinner_move()
        for blob in self.blobs:
            distance = sqrt((blob.center_x - self.player.center_x)**2 + (blob.center_y - self.player.center_y)**2)


            if distance <= 5 * TILE_SIZE and arcade.has_line_of_sight(blob.position, self.player.position, self.walls):
                blob.blob_move(self.map.navmesh, self.player.position)
            else:
                blob.blob_move(self.map.navmesh, None)

        # Détection de collision entre le joueur et les cristaux
        collision_crystals = arcade.check_for_collision_with_list(self.player, self.crystals)
        for crystal in collision_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(self.crystal_sound)
            self.player.score += 1
            self.score_text.text = f"{self.player.score}"

            # Remet le texte de l’arme (ici ce passage pourrait être simplifié


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
        self.update_weapon_text()
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
