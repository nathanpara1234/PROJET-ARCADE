from enemies import *
from enum import Enum
from math import sqrt
import arcade
from constants import *
from textures import *
from player import Direction, Player
from textures import (
    ANIMATION_SWORD_DOWN,
    ANIMATION_SWORD_UP,
    ANIMATION_SWORD_LEFT,
    ANIMATION_SWORD_RIGHT,
)

class Weapon(arcade.TextureAnimationSprite):
    active: bool

    def __init__(self, animation: arcade.TextureAnimation, scale: float) -> None:
        super().__init__(
            animation=animation,
            scale=scale,
            center_x=0,
            center_y=0,
        )
        self.active = False
        self.visible = False

    def deactivate(self) -> None:
        self.active = False
        self.visible = False

    def kill_enemies(self, enemies: arcade.SpriteList[arcade.TextureAnimationSprite]) -> None:
        hit_enemies = arcade.check_for_collision_with_list(self, enemies)
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()

class BoomerangState(Enum):
    INACTIVE = 1
    LAUNCHING = 2
    RETURNING = 3


class Boomerang(Weapon):
    state: BoomerangState
    speed: float
    max_distance: float
    travelled_distance: float

    def __init__(self) -> None:
        # Comme vu dans le cours, une classe qui hérite doit appeler
        # le constructeur de la classe parente avec super().__init__(...)
        super().__init__(
            animation=ANIMATION_BOOMERANG,
            scale=SCALE,
        )
        # Etat initial : le boomerang est inactif et invisible
        self.state = BoomerangState.INACTIVE
        self.visible = False
        # Vitesse conseillée dans l'énoncé
        self.speed = 8
        # Distance maximale : 8 cellules
        self.max_distance = 8 * TILE_SIZE
        # Distance parcourue en phase de lancement
        self.travelled_distance = 0
        # Pas de mouvement au départ
        self.change_x = 0
        self.change_y = 0

    def launch(self, player: Player) -> None:
        """Lance le boomerang depuis la position du joueur.

        Cette méthode ne fait rien si le boomerang n'est pas inactif.
        """
        if self.state != BoomerangState.INACTIVE:
            return

        self.center_x = player.center_x
        self.center_y = player.center_y
        self.travelled_distance = 0
        self.visible = True
        self.state = BoomerangState.LAUNCHING

        if player.direction == Direction.NORTH:
            self.change_x = 0
            self.change_y = self.speed
        elif player.direction == Direction.SOUTH:
            self.change_x = 0
            self.change_y = -self.speed
        elif player.direction == Direction.EAST:
            self.change_x = self.speed
            self.change_y = 0
        elif player.direction == Direction.WEST:
            self.change_x = -self.speed
            self.change_y = 0

    def start_return(self) -> None:
        """Fait passer le boomerang en phase de retour."""
        if self.state == BoomerangState.INACTIVE:
            return

        self.state = BoomerangState.RETURNING
        self.change_x = 0
        self.change_y = 0

    def deactivate(self) -> None:
        """Remet le boomerang dans son état inactif."""
        super().deactivate()
        self.state = BoomerangState.INACTIVE
        self.change_x = 0
        self.change_y = 0
        self.travelled_distance = 0


    def update_boomerang(self,player: Player,walls: arcade.SpriteList[arcade.Sprite],enemies:arcade.SpriteList) -> None:
        """Met à jour le boomerang selon son état.

        - En lancement : il avance en ligne droite.
        - En retour : il revient vers le joueur.
        """
        if self.state == BoomerangState.INACTIVE:
            return

        if self.state == BoomerangState.LAUNCHING:
            self.center_x += self.change_x
            self.center_y += self.change_y

            # On ajoute la distance parcourue à cette frame
            self.travelled_distance += sqrt(self.change_x**2 + self.change_y**2)

            # S'il touche un ennemi, il le tue puis il commence à revenir
            self.kill_enemies(enemies)

            # S'il touche un mur, il revient
            hit_walls = arcade.check_for_collision_with_list(self, walls)
            if hit_walls:
                self.start_return()
                return

            # S'il a atteint sa portée max, il revient
            if self.travelled_distance >= self.max_distance:
                self.start_return()
                return

        elif self.state == BoomerangState.RETURNING:
            dx = player.center_x - self.center_x
            dy = player.center_y - self.center_y
            distance_to_player = sqrt(dx**2 + dy**2)

            # "Suffisamment proche" du joueur
            if distance_to_player <= 12:
                self.deactivate()
                return

            # Normalisation du vecteur pour garder une vitesse constante
            direction_x = dx / distance_to_player
            direction_y = dy / distance_to_player

            self.center_x += direction_x * self.speed
            self.center_y += direction_y * self.speed

            # En retour, il ignore les murs mais tue toujours les ennemis
            hit_enemies = arcade.check_for_collision_with_list(self, enemies)
            for enemy in hit_enemies:
                enemy.remove_from_sprite_lists()

class Sword(Weapon):
    elapsed_time: float

    def __init__(self) -> None:
        # Comme vu dans le cours : une sous-classe doit appeler super().__init__
        super().__init__(
            animation=ANIMATION_SWORD_DOWN,
            scale=2,
        )

    def deactivate(self) -> None:
        super().deactivate()
        self.elapsed_time = 0

    def attack(self, player: Player) -> None:
        # Si l'épée est déjà en cours d'utilisation, on ne fait rien
        if self.active:
            return

        self.active = True
        self.visible = True
        self.elapsed_time = 0

        # Le sprite d'attaque est centré sur le joueur
        self.center_x = player.center_x
        self.center_y = player.center_y

        # Choix de l'animation selon la direction du joueur
        if player.direction == Direction.NORTH:
            self.animation = ANIMATION_SWORD_UP
            self.center_x = player.center_x
            self.center_y = player.center_y + 0.2*TILE_SIZE
        elif player.direction == Direction.SOUTH:
            self.animation = ANIMATION_SWORD_DOWN
            self.center_x = player.center_x
            self.center_y = player.center_y - 0.2*TILE_SIZE
        elif player.direction == Direction.WEST:
            self.animation = ANIMATION_SWORD_LEFT
            self.center_x = player.center_x - 0.2*TILE_SIZE
            self.center_y = player.center_y
        elif player.direction == Direction.EAST:
            self.animation = ANIMATION_SWORD_RIGHT
            self.center_x = player.center_x + 0.2*TILE_SIZE
            self.center_y = player.center_y

        # Redémarrer l'animation depuis le début
        self.time_counter = 0
        self.cur_frame_idx = 0

    def deactivate(self) -> None:
        self.active = False
        self.visible = False
        self.elapsed_time = 0

    def update_sword(self,delta_time: float,enemies: arcade.SpriteList,crystals: arcade.SpriteList[arcade.TextureAnimationSprite],player: Player,crystal_sound : arcade.Sound) -> None:
        if not self.active:
            return
        self.elapsed_time += delta_time

        # Tue les monstres touchés
        self.kill_enemies(enemies)

        # Ramasse aussi les crystals
        hit_crystals = arcade.check_for_collision_with_list(self, crystals)
        for crystal in hit_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(crystal_sound)
            player.score += 1

        # 6 frames * 50 ms = 300 ms = 0.3 seconde
        if self.elapsed_time >= 0.3:
            self.deactivate()
