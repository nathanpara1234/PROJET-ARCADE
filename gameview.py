from typing import Final
import cProfile
import arcade
from text import Text
from world_builder import build_world
from systems import update_camera_position, update_enemies, update_collectibles
from enemies import Enemy, SpinnerSprite
from constants import TILE_SIZE, MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT
from player import Player
from weapons import Boomerang, Sword
from map import Map
from sprite import grid_to_pixels, SwitchSprite, GateSprite, WeaponType
from interactions import (
    restart_if_collision,
    update_spikes,
    restart_if_spikes_collision,
    update_gate_states,
    update_switches_hit_by_sword,
    update_switches_hit_by_boomerang,
)

class GameView(arcade.View):
    grounds: Final[arcade.SpriteList[arcade.Sprite]]
    walls: Final[arcade.SpriteList[arcade.Sprite]]
    crystals: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    keys : Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    chests : Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    spikes: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    spinners: Final[arcade.SpriteList[SpinnerSprite]]
    player_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    holes: Final[arcade.SpriteList[arcade.Sprite]]
    switches: Final[arcade.SpriteList[SwitchSprite]]
    gates: Final[arcade.SpriteList[GateSprite]]
    physics_engine: Final[arcade.PhysicsEngineSimple]
    camera: Final[arcade.camera.Camera2D]
    text : Text
    world_width: Final[int]
    world_height: Final[int]
    boomerang_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    boomerang: Final[Boomerang]
    sword_list: Final[arcade.SpriteList[arcade.TextureAnimationSprite]]
    sword: Final[Sword]
    active_weapon: WeaponType
    enemies: Final[arcade.SpriteList[Enemy]]
    all_enemies: Final[arcade.SpriteList]
    player: Final[Player]
    sword_touched_switches: set[str]
    boomerang_touched_switches: set[str]
    profiler: cProfile.Profile
    spikes_are_active: bool
    spikes_timer: float

    def __init__(self, map: Map) -> None:
        super().__init__()

        self.map = map
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        self.crystal_sound = arcade.load_sound(":resources:sounds/coin5.wav")
        self.chests_sound = arcade.load_sound(":resources:sounds/secret2.wav")
        self.keys_sound = arcade.load_sound(":resources:sounds/upgrade1.wav")
        self.player_list = arcade.SpriteList()
        self.camera = arcade.camera.Camera2D()
        self.world_width = map.width * TILE_SIZE
        self.world_height = map.height * TILE_SIZE
        self.spikes_are_active = True
        self.spikes_timer = 0.0
        self.switches = arcade.SpriteList()
        self.gates = arcade.SpriteList()
        self.sword_touched_switches = set()
        self.boomerang_touched_switches = set()
        self.boomerang_list = arcade.SpriteList()
        self.boomerang = Boomerang()
        self.boomerang_list.append(self.boomerang)
        self.sword_list = arcade.SpriteList()

        world = build_world(self.map)
        self.grounds = world.grounds
        self.walls = world.walls
        self.crystals = world.crystals
        self.keys = world.keys
        self.chests = world.chests
        self.spikes = world.spikes
        self.spinners = world.spinners
        self.holes = world.holes
        self.enemies = world.enemies
        self.all_enemies = world.all_enemies

        for switch_data in self.map.switches:
            self.switches.append(SwitchSprite(switch_data))
        for gate_data in self.map.gates:
            gate = GateSprite(gate_data)
            self.gates.append(gate)
            self.walls.append(gate)
        update_gate_states(self.switches, self.gates, self.walls)

        # on initialise le joueur à sa position de départ
        self.player = Player(grid_to_pixels(map.player_start_x),grid_to_pixels(map.player_start_y),)
        self.player_list.append(self.player)

        # Initialisation de l’épée
        self.sword_list = arcade.SpriteList()
        self.sword = Sword()
        self.sword_list.append(self.sword)
        self.active_weapon = WeaponType.BOOMERANG # au début l'arme par défaut est le boomerang

        # Moteur physique simple : le joueur est bloqué par les murs
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.walls)
        self.profiler = cProfile.Profile()
        self.hud = Text(self.window, self.player, len(self.crystals))


    def on_show_view(self) -> None:
        # Ajuste la taille de la fenêtre à la taille du monde,
        # sans dépasser les dimensions maximales autorisées
        self.window.width = min(MAX_WINDOW_WIDTH, self.world_width)
        self.window.height = min(MAX_WINDOW_HEIGHT, self.world_height)
        self.hud.update_positions()

    def on_draw(self) -> None:
        self.clear()# Efface l’écran puis dessine le monde

        with self.camera.activate():
            self.grounds.draw()
            self.walls.draw()
            self.holes.draw()
            # Les portails et interrupteurs sont dessines comme les autres sprites.
            self.gates.draw()
            self.switches.draw()
            self.crystals.draw()
            self.keys.draw()
            self.chests.draw()
            self.spikes.draw()
            self.spinners.draw()
            if not self.sword.active:  # le sprite d'attaque contient déjà le joueur, évite le doublon
                self.player_list.draw()
            self.boomerang_list.draw()
            self.sword_list.draw()
            self.enemies.draw()
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
            for enemy in self.enemies:
                if isinstance(enemy, Blob) and enemy.path and len(enemy.path) >= 2:
                    arcade.draw_line_strip(enemy.path, arcade.color.RED, 2)'''
        self.hud.draw()

    def restart(self) -> None :
        new_game_view = GameView(self.map)
        self.window.show_view(new_game_view)

    def on_update(self, delta_time: float) -> None:# je relie les switch et les portails à chaque frame
        self.profiler.enable()
        self.do_on_update(delta_time)
        self.profiler.disable()

    def do_on_update(self, delta_time: float) -> None:
        # Met à jour la physique du joueur
        self.physics_engine.update()
        # Met à jour les animations
        self.player.update_animation()
        self.player.player_move()
        if self.player.indestructible:
            self.player.indestructibility_timer -= 1
            if self.player.indestructibility_timer <= 0:
                self.player.indestructible = False
                self.player.indestructibility_timer = 0
        update_camera_position(self.camera, self.player, self.window, self.world_width, self.world_height)
        restart_if_collision(self.player, self.all_enemies, self.holes, self.restart)
        self.crystals.update_animation()
        self.keys.update_animation()
        # on met d'abord à jour l'état du pics en fonction du temps en seconde
        # puis on test la collision (ordre important)
        self.spikes_timer, self.spikes_are_active = update_spikes(self.spikes, self.spikes_timer, self.spikes_are_active, delta_time)
        restart_if_spikes_collision(self.spikes_are_active, self.player, self.spikes, self.restart)
        self.spinners.update_animation()
        self.enemies.update_animation()
        self.boomerang.update_animation()
        self.boomerang.update_boomerang(self.player, self.walls, self.all_enemies)
        self.sword.update_animation()
        self.sword.update_sword(delta_time,self.all_enemies,self.crystals,self.player,self.crystal_sound)
        self.boomerang_touched_switches = update_switches_hit_by_boomerang(self.boomerang, self.boomerang_touched_switches, self.switches)
        self.sword_touched_switches = update_switches_hit_by_sword(self.sword, self.sword_touched_switches, self.switches)
        # Apres les collisions avec les armes, les portails peuvent avoir change.
        update_gate_states(self.switches, self.gates, self.walls)
        update_enemies(self.spinners, self.enemies, self.player, self.walls, self.map.navmesh)
        update_collectibles(self.player, self.crystals, self.crystal_sound, self.keys, self.keys_sound, self.chests, self.chests_sound, self.hud)

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
                self.restart()
            case arcade.key.D:# ici la touche D utilise juste l'arme active
                if self.active_weapon == WeaponType.BOOMERANG:
                    self.boomerang.launch(self.player)
                else:
                    self.sword.attack(self.player)
            case arcade.key.R:# pour changer d'arme il faut utiliser R
                if self.active_weapon == WeaponType.BOOMERANG:
                    self.active_weapon = WeaponType.SWORD
                else:
                    self.active_weapon = WeaponType.BOOMERANG
        self.hud.update_weapon(self.active_weapon)
        self.player.player_move()# recalcule le mouvement du joueur après une touche présse



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
