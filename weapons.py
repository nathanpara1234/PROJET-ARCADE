from enum import Enum, auto
from math import sqrt
from typing import Final
import arcade
from constants import SCALE, BOOMERANG_SPEED, BOOMERANG_MAX_DISTANCE, TILE_SIZE
from textures import (
    ANIMATION_BOOMERANG,
    ANIMATION_SWORD_DOWN,
    ANIMATION_SWORD_UP,
    ANIMATION_SWORD_LEFT,
    ANIMATION_SWORD_RIGHT,
)
from player import Direction, Player


class WeaponType(Enum):
    BOOMERANG = auto()
    SWORD = auto()


class Weapon(arcade.TextureAnimationSprite):
    """Classe de base pour les armes. Fournit desactivate() et kill_enemies() communs à Boomerang et Sword."""

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

    def desactivate(self) -> None:
        """Remet l'arme en état inactif (active=False, visible=False).
        Les sous-classes qui surchargent cette méthode doivent appeler super().desactivate()
        pour garantir que ces deux attributs sont toujours réinitialisés.
        """
        self.active = False
        self.visible = False

    # gère la collision avec les ennemies
    def kill_enemies(self, enemies: arcade.SpriteList[arcade.TextureAnimationSprite]) -> None:# fonction qui enleve les ennemis de la liste arcae sprite
        hit_enemies = arcade.check_for_collision_with_list(self, enemies)
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()

class BoomerangState(Enum):# un enum pour les 3 etats possible d'un boomerang
    INACTIVE = auto()
    LAUNCHING = auto()
    RETURNING = auto()
class Boomerang(Weapon):
    """Arme à trois états (INACTIVE, LAUNCHING, RETURNING) qui revient vers le joueur après avoir été lancée."""
    __state: BoomerangState
    speed: Final[float]
    max_distance: Final[float]
    __travelled_distance: float

    def __init__(self) -> None:
        super().__init__(animation=ANIMATION_BOOMERANG,scale=SCALE,)
        self.__state = BoomerangState.INACTIVE
        self.visible = False
        self.speed = BOOMERANG_SPEED
        self.max_distance = BOOMERANG_MAX_DISTANCE
        # Distance parcourue par le boomerang lorsqu'il est lance
        self.__travelled_distance = 0
        # Pas de mouvement au depart
        self.change_x = 0
        self.change_y = 0

    @property
    def state(self) -> BoomerangState:
        return self.__state

    def launch(self, player: Player) -> None:
        if self.__state != BoomerangState.INACTIVE:# on peut lancer un boomerang seulement si il est inactif
            return
        # on place le boomerang directement au centre du joueur
        self.center_x = player.center_x
        self.center_y = player.center_y
        self.__travelled_distance = 0
        self.visible = True
        self.__state = BoomerangState.LAUNCHING
        # le boomerang doit partir dans la direction où regarde le joueur
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

    def start_return(self) -> None:# lorsque le boomerang doit revenir on change juste son etat
        if self.__state == BoomerangState.INACTIVE:
            return
        self.__state = BoomerangState.RETURNING
        self.change_x = 0
        self.change_y = 0

    def desactivate(self) -> None:#on remet le boomerang dans son état inactif
        # on ne supprime pas le sprite juste on le rend inactif ce qui est plus facile lorsuq'on veut le réactiver
        super().desactivate()# on le rend invisible et non active
        self.__state = BoomerangState.INACTIVE
        # il revient au centre du joueur
        self.change_x = 0
        self.change_y = 0
        self.__travelled_distance = 0


    def update_boomerang(self,player: Player,walls: arcade.SpriteList[arcade.Sprite],enemies:arcade.SpriteList) -> None:
        if self.state == BoomerangState.INACTIVE:# si le boomerang n'est pas lancé je fais rien
            return
        if self.state == BoomerangState.LAUNCHING:
            # le boomerang avance tout droit à chaque frame j'ajoute la longueur du déplacement
            self.center_x += self.change_x
            self.center_y += self.change_y
            # On ajoute la distance parcourue a cette frame
            self.__travelled_distance += sqrt(self.change_x**2 + self.change_y**2)
            # si il touche un ennemi il le supprime et il revient
            self.kill_enemies(enemies)
            # si il touche un mur il revient aussi
            hit_walls = arcade.check_for_collision_with_list(self, walls)
            if hit_walls:
                self.start_return()
                return
            # si la distance parcouru atteint la distance maximale parcourable il revient
            if self.__travelled_distance >= self.max_distance:
                self.start_return()
                return

        elif self.state == BoomerangState.RETURNING:
            # pour revenir vers le joueur on calcule le vecteur entre le boomerang et le joueur
            dx = player.center_x - self.center_x
            dy = player.center_y - self.center_y
            distance_to_player = sqrt(dx**2 + dy**2)
            # lorsqu'il est suffisamment proche du joueur on le desactive
            if distance_to_player <= 12:
                self.desactivate()
                return

            # on normalise la direction du vecteur entre le joueur et le boomerang
            direction_x = dx / distance_to_player
            direction_y = dy / distance_to_player
            # puis le boomerang avance vers le joueur
            self.center_x += direction_x * self.speed
            self.center_y += direction_y * self.speed

            # il tue aussi les ennemis lorsqu'il revient
            hit_enemies = arcade.check_for_collision_with_list(self, enemies)
            for enemy in hit_enemies:
                enemy.remove_from_sprite_lists()

class Sword(Weapon):
    """Arme de mêlée qui frappe dans la direction du joueur pendant une courte durée fixe."""

    __elapsed_time: float

    def __init__(self) -> None:
        super().__init__(animation=ANIMATION_SWORD_DOWN,scale=2,)
        self.__elapsed_time = 0

    def attack(self, player: Player) -> None:
        # Si l'épée est en train d'être utilisé meme si on appuie sur D ça ne change rien
        if self.active:
            return
        # on active ensuite l'epee
        self.active = True
        self.visible = True
        self.__elapsed_time = 0


        self.center_x = player.center_x
        self.center_y = player.center_y

        # dans la consigne on dit que l'épee apparait du côté où le joueur regarde
        # On choisit donc l'animation de l'épee selon la direction du joueur
        if player.direction == Direction.NORTH:
            self.animation = ANIMATION_SWORD_UP
            self.center_x = player.center_x
            # le sprite de l'épee n'est pas centré sur le joueur
            # un peu décalé sinon on ne peut pas tuer
            self.center_y = player.center_y + 0.3*TILE_SIZE
        elif player.direction == Direction.SOUTH:
            self.animation = ANIMATION_SWORD_DOWN
            self.center_x = player.center_x
            self.center_y = player.center_y - 0.3*TILE_SIZE
        elif player.direction == Direction.WEST:
            self.animation = ANIMATION_SWORD_LEFT
            self.center_x = player.center_x - 0.3*TILE_SIZE
            self.center_y = player.center_y
        elif player.direction == Direction.EAST:
            self.animation = ANIMATION_SWORD_RIGHT
            self.center_x = player.center_x + 0.3*TILE_SIZE
            self.center_y = player.center_y

        # à chaque nouvelle attaque l'animation repart depuis le début
        self.time_counter = 0
        self.cur_frame_idx = 0

    def desactivate(self) -> None:# fonction qui quand on l'applique desactive l'epée
        self.active = False
        self.visible = False
        self.__elapsed_time = 0

    def update_sword(self, delta_time: float, enemies: arcade.SpriteList) -> None:
        if not self.active:
            return
        self.__elapsed_time += delta_time
        self.kill_enemies(enemies)
        if self.__elapsed_time >= 0.3:
            self.desactivate()
