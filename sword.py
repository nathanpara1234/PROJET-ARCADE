import arcade  

from textures import (
    ANIMATION_SWORD_DOWN,
    ANIMATION_SWORD_UP,
    ANIMATION_SWORD_LEFT,
    ANIMATION_SWORD_RIGHT,
)
from player import Player, Direction


class Sword(arcade.TextureAnimationSprite):
    active: bool
    elapsed_time: float

    def __init__(self) -> None:
        # Comme vu dans le cours : une sous-classe doit appeler super().__init__
        super().__init__(
            animation=ANIMATION_SWORD_DOWN,
            scale=1,
            center_x=0,
            center_y=0,
        )

        self.active = False
        self.elapsed_time = 0
        self.visible = False

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
        elif player.direction == Direction.SOUTH:
            self.animation = ANIMATION_SWORD_DOWN
        elif player.direction == Direction.WEST:
            self.animation = ANIMATION_SWORD_LEFT
        elif player.direction == Direction.EAST:
            self.animation = ANIMATION_SWORD_RIGHT

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
        hit_enemies = arcade.check_for_collision_with_list(self, enemies)
        for enemy in hit_enemies:
            enemy.remove_from_sprite_lists()

        # Ramasse aussi les crystals
        hit_crystals = arcade.check_for_collision_with_list(self, crystals)
        for crystal in hit_crystals:
            crystal.remove_from_sprite_lists()
            arcade.play_sound(crystal_sound)
            player.score += 1

        # 6 frames * 50 ms = 300 ms = 0.3 seconde
        if self.elapsed_time >= 0.3:
            self.deactivate()
