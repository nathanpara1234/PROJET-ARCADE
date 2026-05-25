from enum import Enum
from math import sqrt
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

    def desactivate(self) -> None:
        self.active = False
        self.visible = False

    def kill_enemies(self, enemies: arcade.SpriteList[arcade.TextureAnimationSprite]) -> None:# fonction qui enleve les ennemis de la liste arcae sprite
        hit_enemies = arcade.check_for_collision_with_list(self, enemies)
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()

class BoomerangState(Enum):# un enum pour les 3 etats possible d'un boomerang
    INACTIVE = 1
    LAUNCHING = 2
    RETURNING = 3
class Boomerang(Weapon):
    state: BoomerangState
    speed: float
    max_distance: float
    travelled_distance: float

    def __init__(self) -> None:
        super().__init__(animation=ANIMATION_BOOMERANG,scale=SCALE,)
        self.state = BoomerangState.INACTIVE
        self.visible = False
        self.speed = BOOMERANG_SPEED
        self.max_distance = BOOMERANG_MAX_DISTANCE
        # Distance parcourue par le boomerang lorsqu'il est lancé
        self.travelled_distance = 0
        # Pas de mouvement au départ
        self.change_x = 0
        self.change_y = 0

    def launch(self, player: Player) -> None:
        if self.state != BoomerangState.INACTIVE:# on peut lancer un boomerang seulement si il est inactif
            return
        # on place le boomerang directement au centre du joueur
        self.center_x = player.center_x
        self.center_y = player.center_y
        self.travelled_distance = 0
        self.visible = True
        self.state = BoomerangState.LAUNCHING
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
        if self.state == BoomerangState.INACTIVE:
            return
        self.state = BoomerangState.RETURNING
        self.change_x = 0
        self.change_y = 0

    def deactivate(self) -> None:#on remet le boomerang dans son état inactif
        # on ne supprime pas le sprite juste on le rend inactif ce qui est plus facile lorsuq'on veut le réactiver
        super().desactivate()# on le rend invisible et non active
        self.state = BoomerangState.INACTIVE
        # il revient au centre du jooueur
        self.change_x = 0
        self.change_y = 0
        self.travelled_distance = 0


    def update_boomerang(self,player: Player,walls: arcade.SpriteList[arcade.Sprite],enemies:arcade.SpriteList) -> None:
        if self.state == BoomerangState.INACTIVE:# si le boomerang n'est pas lancé je fais rien
            return
        if self.state == BoomerangState.LAUNCHING:
            # le boomerang avance tout droit à chaque frame j'ajoute la longueur du déplacement
            self.center_x += self.change_x
            self.center_y += self.change_y
            # On ajoute la distance parcourue à cette frame
            self.travelled_distance += sqrt(self.change_x**2 + self.change_y**2)
            # si il touche un ennemi il le supprime et il revient
            self.kill_enemies(enemies)
            # si il touche unu mur il revient aussi
            hit_walls = arcade.check_for_collision_with_list(self, walls)
            if hit_walls:
                self.start_return()
                return
            # si la distance parcouru atteint la distance maximale parcourable il revient
            if self.travelled_distance >= self.max_distance:
                self.start_return()
                return

        elif self.state == BoomerangState.RETURNING:
            # pour revenir vers le joueur on calcule le vecteur entre le boomerang et le joueur
            dx = player.center_x - self.center_x
            dy = player.center_y - self.center_y
            distance_to_player = sqrt(dx**2 + dy**2)
            # lorsqu'il est suffisamment proche du joueur on le desactive
            if distance_to_player <= 12:
                self.deactivate()
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
    elapsed_time: float

    def __init__(self) -> None:
        super().__init__(animation=ANIMATION_SWORD_DOWN,scale=2,)

    def desactivate(self) -> None:
        super().desactivate()
        self.elapsed_time = 0

    def attack(self, player: Player) -> None:
        # Si l'épée est en train d'être utilisé meme si on appuie sur D ça ne change rien
        if self.active:
            return
        # on active ensuite l'epee
        self.active = True
        self.visible = True
        self.elapsed_time = 0

        # Le sprite de l'épee est centré sur le joueur
        self.center_x = player.center_x
        self.center_y = player.center_y

        # dans la consigne on dit que l'épee apparait du côté où le joueur regarde
        # On choisit donc l'animation de l'épee selon la direction du joueur
        if player.direction == Direction.NORTH:
            self.animation = ANIMATION_SWORD_UP
            self.center_x = player.center_x
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

        # A chaque nouvelle attaque l'animation repart depuis le début
        self.time_counter = 0
        self.cur_frame_idx = 0

    def desactivate(self) -> None:# fonction qui quand on l'applique desactive l'epée
        self.active = False
        self.visible = False
        self.elapsed_time = 0

    def update_sword(self,delta_time: float,enemies: arcade.SpriteList,crystals: arcade.SpriteList[arcade.TextureAnimationSprite],player: Player,crystal_sound : arcade.Sound) -> None:
        if not self.active:# si l'epée n'est pas active on fait rien
            return
        self.elapsed_time += delta_time # si elle est active on comptes le temps
        self.kill_enemies(enemies)# l'épee tue les ennemis touché
        hit_crystals = arcade.check_for_collision_with_list(self, crystals)# ramasse aussi les crystals
        for crystal in hit_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(crystal_sound)
            player.score += 1
        if self.elapsed_time >= 0.3:# l'épee agit durant 6 frames soit 6*50ms = 300ms = 0.3s
            self.desactivate()
