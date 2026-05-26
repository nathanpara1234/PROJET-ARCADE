import arcade
from pyglet.graphics import Batch
from player import Player
from sprite import WeaponType


class Text:
    def __init__(self, window: arcade.Window, player: Player, total_crystals: int) -> None:
        self.window = window
        self.total_crystals = total_crystals
        self.camera = arcade.camera.Camera2D()
        self.batch = Batch()

        self.score_text = arcade.Text(
            text=f"{player.score} / {total_crystals}",
            x=20,
            y=window.height - 40,
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.batch,
        )

        self.key_text = arcade.Text(
            text=f"Clés : {player.key}",
            x=window.width - 20,
            y=window.height - 40,
            color=arcade.color.WHITE,
            font_size=18,
            anchor_x="right",
            batch=self.batch,
        )

        self.weapon_text = arcade.Text(
            text="Arme : Boomerang",
            x=20,
            y=window.height - 100,
            color=arcade.color.WHITE,
            font_size=18,
            batch=self.batch,
        )

        self.end_text = arcade.Text(
            text="",
            x=window.width // 2,
            y=window.height // 2,
            color=arcade.color.YELLOW,
            font_size=72,
            anchor_x="center",
            anchor_y="center",
            batch=self.batch,
        )


    def update_score(self, player: Player) -> None:
        self.score_text.text = f"{player.score} / {self.total_crystals}"

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



