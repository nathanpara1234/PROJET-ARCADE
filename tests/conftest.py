import sys
import warnings
from pathlib import Path

import arcade
from arcade import gl
import pytest


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


WINDOW: arcade.Window | None = None


def create_window() -> arcade.Window:
    global WINDOW
    if not WINDOW:
        WINDOW = arcade.Window(
            width=800, height=600, title="Testing", antialiasing=False
        )
    return WINDOW


def prepare_window(window: arcade.Window, caption: str) -> None:
    if window.has_exit:
        raise RuntimeError("Please do not close the global test window.")

    window.switch_to()
    window.set_size(800, 600)
    window.set_caption(caption)

    ctx = window.ctx
    arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.LINEAR, gl.LINEAR
    window._start_finish_render_data = None
    window.hide_view()
    window.dispatch_pending_events()
    try:
        arcade.disable_timings()
    except Exception:
        pass

    ctx.reset()
    window.set_vsync(False)
    window.flip()
    window.clear()
    window.default_camera.use()
    ctx.gc_mode = "context_gc"
    ctx.gc()


@pytest.fixture
def window_caption(request: pytest.FixtureRequest) -> str:
    return f"Testing - {request.node.name}"


@pytest.fixture(scope="function")
def window(window_caption: str) -> arcade.Window:
    window = create_window()
    arcade.set_window(window)
    prepare_window(window, caption=window_caption)
    return window
