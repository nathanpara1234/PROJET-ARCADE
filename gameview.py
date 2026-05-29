import cProfile
import arcade
from text import Text
from world_builder import GateSprite, SwitchSprite, WorldSprites, InteractionSprites, build_world, grid_to_pixels, switch_gate_interactions
from systems import update_camera_position, update_enemies, update_collectibles
from enemies import Enemy, SpinnerSprite, Blob
from constants import TILE_SIZE, MAX_WINDOW_WIDTH, MAX_WINDOW_HEIGHT, DRAW_NAVMESHES
from player import Player
from weapons import Boomerang, Sword, WeaponType
from map import Map
from interactions import (
    should_restart_after_collision,
    update_spikes,
    should_restart_after_spikes_collision,
    update_gate_states,
    update_switches_hit_by_sword,
    update_switches_hit_by_boomerang,
)

class GameView(arcade.View):
    world: WorldSprites
    interactions: InteractionSprites
    physics_engine: arcade.PhysicsEngineSimple
    camera: arcade.camera.Camera2D
    text : Text
    boomerang_list: arcade.SpriteList[arcade.TextureAnimationSprite]
    boomerang: Boomerang
    sword_list: arcade.SpriteList[arcade.TextureAnimationSprite]
    sword: Sword
    active_weapon: WeaponType
    player_list: arcade.SpriteList[arcade.TextureAnimationSprite]
    player: Player
    sword_touched_switches: set[str]
    boomerang_touched_switches: set[str]
    profiler: cProfile.Profile
    spikes_are_active: bool
    spikes_timer: float

    @property
    def world_width(self) -> int:
        return self.map.width * TILE_SIZE

    @property
    def world_height(self) -> int:
        return self.map.height * TILE_SIZE

    def __init__(self, map: Map) -> None:
        super().__init__()

        self.map = map
        self.background_color = arcade.csscolor.CORNFLOWER_BLUE

        self.crystal_sound = arcade.load_sound(":resources:sounds/coin5.wav")
        self.chests_sound = arcade.load_sound(":resources:sounds/secret2.wav")
        self.keys_sound = arcade.load_sound(":resources:sounds/upgrade1.wav")
        self.player_list = arcade.SpriteList()
        self.camera = arcade.camera.Camera2D()

        self.spikes_are_active = True
        self.spikes_timer = 0.0
        self.sword_touched_switches = set()
        self.boomerang_touched_switches = set()
        self.boomerang_list = arcade.SpriteList()
        self.boomerang = Boomerang()
        self.boomerang_list.append(self.boomerang)
        self.sword_list = arcade.SpriteList()

        self.world = build_world(self.map)
        self.interactions = switch_gate_interactions(self.map, self.world.walls)

        # on initialise le joueur à sa position de départ
        self.player = Player(grid_to_pixels(map.player_start_x),grid_to_pixels(map.player_start_y),)
        self.player_list.append(self.player)

        # Initialisation de l'épee
        self.sword_list = arcade.SpriteList()
        self.sword = Sword()
        self.sword_list.append(self.sword)
        self.active_weapon = WeaponType.BOOMERANG # au début l'arme par défaut est le boomerang
        self.physics_engine = arcade.PhysicsEngineSimple(self.player, self.world.walls)
        self.profiler = cProfile.Profile()
        self.text = Text(self.window, self.player, len(self.world.crystals))


    def on_show_view(self) -> None:
        # ajuste la taille de la fenetre à  la taille du monde,
        # sans dépasser les dimensions maximales autorisees
        self.window.width = min(MAX_WINDOW_WIDTH, self.world_width)
        self.window.height = min(MAX_WINDOW_HEIGHT, self.world_height)

    def on_draw(self) -> None:
        self.clear()#efface l'écran puis dessine le monde

        with self.camera.activate():
            self.world.grounds.draw()
            self.world.walls.draw()
            self.world.holes.draw()
            self.interactions.gates.draw()
            self.interactions.switches.draw()
            self.world.crystals.draw()
            self.world.keys.draw()
            self.world.chests.draw()
            self.world.spikes.draw()
            self.world.spinners.draw()
            if not self.sword.active:  # evite le probleme du double joueur avec l'epee
                self.player_list.draw()
            self.boomerang_list.draw()
            self.sword_list.draw()
            self.world.enemies.draw()

        self.text.draw()

    def restart(self) -> None :
        new_game_view = GameView(self.map)
        self.window.show_view(new_game_view)

    def on_update(self, delta_time: float) -> None:# relie les switch et les portails à chaque frame
        self.profiler.enable()
        self.do_on_update(delta_time)
        self.profiler.disable()

    def do_on_update(self, delta_time: float) -> None:
        # Mise jour la physique du joueur
        self.physics_engine.update()
        # Met à jour les animations
        self.player.update_animation()
        self.player.player_move()
        self.player.update_invincibility()
        update_camera_position(self.camera, self.player, self.window, self.world_width, self.world_height)
        if should_restart_after_collision(self.player, self.world.all_enemies, self.world.holes):
            self.restart()
            return
        self.world.crystals.update_animation()
        self.world.keys.update_animation()
        # on met d'abord à jour l'état du pics en fonction du temps en seconde
        # puis on test la collision (ordre important)
        self.spikes_timer, self.spikes_are_active = update_spikes(self.world.spikes, self.spikes_timer, self.spikes_are_active, delta_time)
        if should_restart_after_spikes_collision(self.spikes_are_active, self.player, self.world.spikes):
            self.restart()
            return
        self.world.spinners.update_animation()
        self.world.enemies.update_animation()
        self.boomerang.update_animation()
        self.boomerang.update_boomerang(self.player, self.world.walls, self.world.all_enemies)
        self.sword.update_animation()
        self.sword.update_sword(delta_time, self.world.all_enemies)
        self.boomerang_touched_switches = update_switches_hit_by_boomerang(self.boomerang, self.boomerang_touched_switches, self.interactions.switches)
        self.sword_touched_switches = update_switches_hit_by_sword(self.sword, self.sword_touched_switches, self.interactions.switches)
        # pres les collisions avec les armes, les portails peuvent avoir change.
        update_gate_states(self.interactions.switches, self.interactions.gates, self.world.walls)
        update_enemies(self.world.spinners, self.world.enemies, self.player, self.world.walls, self.map.navmesh)
        update_collectibles(self.player, self.sword, self.world.crystals, self.crystal_sound, self.world.keys, self.keys_sound, self.world.chests, self.chests_sound, self.text)

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
            case arcade.key.D:
                if self.active_weapon == WeaponType.BOOMERANG:
                    self.boomerang.launch(self.player)
                else:
                    self.sword.attack(self.player)
            case arcade.key.R:# pour changer d'arme il faut utiliser R
                if self.active_weapon == WeaponType.BOOMERANG:
                    self.active_weapon = WeaponType.SWORD
                else:
                    self.active_weapon = WeaponType.BOOMERANG
        self.text.update_weapon(self.active_weapon)
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
