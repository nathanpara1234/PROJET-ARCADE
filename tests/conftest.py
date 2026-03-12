from map import MAP_DECOUVERTE
import arcade
from arcade import gl
import pytest
from gameview import GameView

# This file must be named 'conftest.py' and be located in the 'tests/' directory.
# It gets loaded automatically by pytest to provide "fixtures" available to all tests.
# In our context, it allows test functions to require a `window: arcade.Window`
# argument (the name is meaningful!). It will be the one and only Window used
# for testing. Tests are not allowed to create their own Window.
# We copied this from the arcade open source repository, and simplified it
# because we do not need all their configurations.
#
# You should not modify this file, and you do not need to understand what it does.

WINDOW: arcade.Window | None = None

def create_window() -> arcade.Window:
    global WINDOW
    if not WINDOW:
        WINDOW = arcade.Window(
            width=800, height=600, title="Testing", antialiasing=False
        )
    return WINDOW

def prepare_window(window: arcade.Window, caption: str) -> None:
    # Check if someone has been naughty
    if window.has_exit:
        raise RuntimeError("Please do not close the global test window :D")

    window.switch_to()
    window.set_size(800, 600)
    window.set_caption(caption)

    ctx = window.ctx
    arcade.SpriteList.DEFAULT_TEXTURE_FILTER = gl.LINEAR, gl.LINEAR
    window._start_finish_render_data = None
    window.hide_view()  # Disable views if any is active
    window.dispatch_pending_events()
    try:
        arcade.disable_timings()
    except Exception:
        pass

    # Reset context (various states)
    ctx.reset()
    window.set_vsync(False)
    window.flip()
    window.clear()
    window.default_camera.use()
    ctx.gc_mode = "context_gc"
    ctx.gc()

@pytest.fixture
def test_name(request: pytest.FixtureRequest) -> str:
    return f"Testing - {request.node.name}"

@pytest.fixture(scope="function")
def window(test_name: str) -> arcade.Window:
    """
    Global window that is shared between tests.

    This just returns the global window, but ensures that the context
    is reset between each test function and the window is flipped
    between each test function.
    """
    window = create_window()
    arcade.set_window(window)
    prepare_window(window, caption=test_name)
    return window


def test_collect_crystals(window: arcade.Window) -> None:
    view = GameView(MAP_DECOUVERTE)
    window.show_view(view)

    INITIAL_CRYSTAL_COUNT = 3

    # Make sure we have the amount of coins we expect at the start
    assert len(view.crystals) == INITIAL_CRYSTAL_COUNT

    # Start moving right
    view.on_key_press(arcade.key.RIGHT, 0)

    # Let the game run for 1 second
    window.test(60)

    # We should have collected the first coin
    assert len(view.crystals) == INITIAL_CRYSTAL_COUNT - 1

    # Stop moving right, move up
    view.on_key_release(arcade.key.RIGHT, 0)
    view.on_key_press(arcade.key.UP, 0)

    # Let the game run for 1 more second
    window.test(60)

    # We should have collected the second coin
    assert len(view.crystals) == INITIAL_CRYSTAL_COUNT - 2
