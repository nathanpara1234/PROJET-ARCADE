from dataclasses import dataclass
import arcade

from constants import TILE_SIZE, SCALE, SPINNER_SPEED
from enemies import Bat, Blob, SpinnerSprite, compute_horizontal_spinner_limits, compute_vertical_spinner_limits
from gate_condition import GateCondition
from map import Map, GridCell, SwitchData, GateData

from textures import (
    TEXTURE_GRASS,
    TEXTURE_BUSH,
    TEXTURE_HOLE,
    ANIMATION_CRYSTALS,
    ANIMATION_KEY,
    ANIMATION_CHEST,
    ANIMATION_SPIKES,
    ANIMATION_SPINNER,
    TEXTURE_SWITCH_OFF,
    TEXTURE_SWITCH_ON,
    TEXTURE_GATE_OPEN,
    TEXTURE_GATE_CLOSED,
)

def grid_to_pixels(i: int) -> int:
    return i * TILE_SIZE + (TILE_SIZE // 2)


def make_tile_sprite(texture: arcade.Texture, x: int, y: int) -> arcade.Sprite:
    return arcade.Sprite(
        texture,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )


def make_tile_animation_sprite(
    animation: arcade.TextureAnimation,
    x: int,
    y: int,
) -> arcade.TextureAnimationSprite:
    return arcade.TextureAnimationSprite(
        animation=animation,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )



class SwitchSprite(arcade.Sprite):
    id: str
    is_on: bool

    def __init__(self, switch: SwitchData) -> None:
        texture = TEXTURE_SWITCH_ON if switch.is_on else TEXTURE_SWITCH_OFF
        super().__init__(
            texture,
            scale=0.25,
            center_x=grid_to_pixels(switch.x),
            center_y=grid_to_pixels(switch.y),
        )
        self.id = switch.id
        self.is_on = switch.is_on

    def inverse_state_switch(self) -> None:
        self.is_on = not self.is_on
        if self.is_on:
            self.texture = TEXTURE_SWITCH_ON
        else:
            self.texture = TEXTURE_SWITCH_OFF


class GateSprite(arcade.Sprite):
    open_if: GateCondition
    is_open: bool

    def __init__(self, gate: GateData) -> None:
        super().__init__(
            TEXTURE_GATE_CLOSED,
            scale=SCALE,
            center_x=grid_to_pixels(gate.x),
            center_y=grid_to_pixels(gate.y),
        )
        self.open_if = gate.open_if
        self.is_open = False

    def set_open(self, is_open: bool) -> None:
        self.is_open = is_open
        if self.is_open:
            self.texture = TEXTURE_GATE_OPEN
        else:
            self.texture = TEXTURE_GATE_CLOSED


@dataclass
class InteractionSprites:
    switches: arcade.SpriteList
    gates: arcade.SpriteList


@dataclass
class WorldSprites:
    # Regroupe toutes les SpriteList construites depuis la map et
    # GameView recupere cet objet au lieu de creer chaque liste lui-meme
    grounds: arcade.SpriteList[arcade.Sprite]
    walls: arcade.SpriteList[arcade.Sprite]
    crystals: arcade.SpriteList[arcade.TextureAnimationSprite]
    keys: arcade.SpriteList[arcade.TextureAnimationSprite]
    chests: arcade.SpriteList[arcade.TextureAnimationSprite]
    spikes: arcade.SpriteList[arcade.TextureAnimationSprite]
    spinners: arcade.SpriteList[SpinnerSprite]
    holes: arcade.SpriteList[arcade.Sprite]
    enemies: arcade.SpriteList
    all_enemies: arcade.SpriteList


def make_spinner(game_map: Map, x: int, y: int, is_horizontal: bool) -> SpinnerSprite:
    # Fabrique un spinner et configure ses bornes de deplacement
    # les bornes sont calculees une seule fois au chargement du monde
    spinner = SpinnerSprite(
        animation=ANIMATION_SPINNER,
        scale=SCALE,
        center_x=grid_to_pixels(x),
        center_y=grid_to_pixels(y),
    )

    spinner.is_horizontal = is_horizontal

    if is_horizontal:
        # pour spinner horizontal il se deplace entre deux limites sur la coordonnée x
        left_x, right_x = compute_horizontal_spinner_limits(game_map, x, y)
        spinner.min_pos = grid_to_pixels(left_x)
        spinner.max_pos = grid_to_pixels(right_x)
        spinner.change_x = SPINNER_SPEED
        spinner.change_y = 0
    else:
        # spinner vertical meme chose mais sur y
        bottom_y, top_y = compute_vertical_spinner_limits(game_map, x, y)
        spinner.min_pos = grid_to_pixels(bottom_y)
        spinner.max_pos = grid_to_pixels(top_y)
        spinner.change_x = 0
        spinner.change_y = SPINNER_SPEED

    return spinner


def build_world(game_map: Map) -> WorldSprites:
    # les listes statiques utilisent un spatial hash pour accelerer les collisions
    grounds = arcade.SpriteList(use_spatial_hash=True)
    walls = arcade.SpriteList(use_spatial_hash=True)
    crystals = arcade.SpriteList(use_spatial_hash=True)
    keys = arcade.SpriteList(use_spatial_hash=True)
    chests = arcade.SpriteList(use_spatial_hash=True)
    spikes = arcade.SpriteList(use_spatial_hash=True)
    spinners = arcade.SpriteList()
    holes = arcade.SpriteList()
    enemies = arcade.SpriteList()
    all_enemies = arcade.SpriteList()

    # On parcourt la map abstraite cellule par cellule et chaque GridCell decide quel sprite doit etre cree
    for x in range(game_map.width):
        for y in range(game_map.height):
            # chaque case recoit toujours une herbe de fond
            grounds.append(make_tile_sprite(TEXTURE_GRASS, x, y))
            cell = game_map.get(x, y)

            if cell == GridCell.BUSH:
                # buissons bloquent le joueur, ils vont donc dans walls
                walls.append(make_tile_sprite(TEXTURE_BUSH, x, y))

            elif cell == GridCell.CRYSTAL:
                crystals.append(make_tile_animation_sprite(ANIMATION_CRYSTALS, x, y))

            elif cell == GridCell.KEY:
                keys.append(make_tile_animation_sprite(ANIMATION_KEY, x, y))

            elif cell == GridCell.CHEST:
                chests.append(make_tile_animation_sprite(ANIMATION_CHEST, x, y))

            elif cell == GridCell.SPIKES:
                spikes.append(make_tile_animation_sprite(ANIMATION_SPIKES, x, y))

            elif cell == GridCell.SPINNER_HORIZONTAL or cell == GridCell.SPINNER_VERTICAL:
                # Les spinners ont leur propre liste pour leur mouvement,
                # et all_enemies sert aux collisions communes avec les armes ou joueur
                spinner = make_spinner(
                    game_map,
                    x,
                    y,
                    is_horizontal=(cell == GridCell.SPINNER_HORIZONTAL),
                )
                spinners.append(spinner)
                all_enemies.append(spinner)

            elif cell == GridCell.HOLE:
                holes.append(make_tile_sprite(TEXTURE_HOLE, x, y))

            elif cell == GridCell.BAT:
                # Bat et Blob heritent de Enemy et sont donc dans enemies
                bat = Bat(
                    start_x=grid_to_pixels(x),
                    start_y=grid_to_pixels(y),
                    world_width=game_map.width * TILE_SIZE,
                    world_height=game_map.height * TILE_SIZE,
                )
                enemies.append(bat)
                all_enemies.append(bat)

            elif cell == GridCell.BLOB:
                # Le blob a besoin de connaitre les dimensions du monde pour sa patrouille et recherche de target
                blob = Blob(
                    start_x=grid_to_pixels(x),
                    start_y=grid_to_pixels(y),
                    world_width=game_map.width * TILE_SIZE,
                    world_height=game_map.height * TILE_SIZE,
                )
                enemies.append(blob)
                all_enemies.append(blob)

    return WorldSprites(
        grounds=grounds,
        walls=walls,
        crystals=crystals,
        keys=keys,
        chests=chests,
        spikes=spikes,
        spinners=spinners,
        holes=holes,
        enemies=enemies,
        all_enemies=all_enemies,
    )


def switch_gate_interactions(
    game_map: Map,
    walls: arcade.SpriteList,
) -> InteractionSprites:
    from interactions import update_gate_states

    switches: arcade.SpriteList = arcade.SpriteList()
    gates: arcade.SpriteList = arcade.SpriteList()

    for switch_data in game_map.switches:
        switches.append(SwitchSprite(switch_data))

    for gate_data in game_map.gates:
        gate = GateSprite(gate_data)
        gates.append(gate)
        walls.append(gate)

    update_gate_states(switches, gates, walls)
    return InteractionSprites(switches=switches, gates=gates)
