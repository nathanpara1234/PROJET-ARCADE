import arcade
from pyglet.graphics import Batch
from player import Player
from sprite import WeaponType


class Text:
    def __init__(self, window: arcade.Window, player: Player, total_crystals: int) -> None:
        self.window = window
        self.camera = arcade.camera.Camera2D()
        self.batch = Batch()

        self.score_text = arcade.Text(
            text=f"{player.score} / {total_crystals}",
            x=20,
            y=window.height - 40,      # position provisoire, recalculée dans update_positions
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.batch,
        )

        self.key_text = arcade.Text(
            text=f"Clés : {player.key}",
            x=20,                      # position provisoire, recalculée dans update_positions
            y=window.height - 70,      # position provisoire, recalculée dans update_positions
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.batch,
        )

        self.weapon_text = arcade.Text(
            text="Arme : Boomerang",
            x=20,                      # position provisoire, recalculée dans update_positions
            y=window.height - 70,      # position provisoire, recalculée dans update_positions
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.batch,
        )

        self.end_text = arcade.Text(
            text="",
            x=window.width // 2,       # position provisoire, recalculée dans update_positions
            y=window.height // 2,      # position provisoire, recalculée dans update_positions
            color=arcade.color.YELLOW,
            font_size=72,
            anchor_x="center",
            anchor_y="center",
            batch=self.batch,
        )

    def update_positions(self) -> None:
        # recalcule les positions après redimensionnement pour qu'elles soient toujours visibles
        self.score_text.y = self.window.height - 40        # score en haut à gauche
        self.key_text.x = 20                               # clés en haut à gauche
        self.key_text.y = self.window.height - 70          # clés sous le score
        self.weapon_text.x = self.window.width // 2        # arme au centre horizontalement
        self.weapon_text.y = self.window.height - 70       # arme légèrement en dessous des clés
        self.end_text.x = self.window.width // 2           # texte de fin centré horizontalement
        self.end_text.y = self.window.height // 2          # texte de fin centré verticalement

    def update_score(self, player: Player, total_crystals: int) -> None:
        self.score_text.text = f"{player.score} / {total_crystals}"

    def update_keys(self, player: Player) -> None:
        self.key_text.text = f"Clés : {player.key}"

    def update_weapon(self, active_weapon: WeaponType) -> None:
        if active_weapon == WeaponType.BOOMERANG:
            self.weapon_text.text = "Arme : Boomerang"
        else:
            self.weapon_text.text = "Arme : Épée"

    def show_end(self) -> None:
        self.end_text.text = "END"

    def draw(self) -> None:
        with self.camera.activate():
            self.batch.draw()
