from textwrap import dedent

import pytest

from gate_conditions import condition_is_true
from map import GridCell, InvalidMapFileException, load_map_from_string


def test_condition_is_true_without_arcade() -> None:
    condition = {
        "and": [
            {"switch_is_on": "first"},
            {"not": [{"switch_is_on": "second"}]},
        ]
    }

    assert condition_is_true(condition, {"first": True, "second": False})
    assert not condition_is_true(condition, {"first": True, "second": True})


def test_load_switch_and_gate_from_yaml() -> None:
    text = dedent("""\
        width: 5
        height: 3
        switches:
          - id: first
            x: 1
            y: 1
            state: on
        gates:
          - x: 3
            y: 1
            open_if:
              switch_is_on: first
        ---
        xxxxx
        x^ |x
        xxxxx
        ---
    """)

    game_map = load_map_from_string(text)

    assert game_map.get(1, 1) == GridCell.SWITCH
    assert game_map.get(3, 1) == GridCell.GATE
    assert game_map.switches[0].id == "first"
    assert game_map.switches[0].is_on
    assert game_map.gates[0].open_if == {"switch_is_on": "first"}


def test_gate_cannot_use_unknown_switch() -> None:
    text = dedent("""\
        width: 5
        height: 3
        gates:
          - x: 3
            y: 1
            open_if:
              switch_is_on: missing
        ---
        xxxxx
        x  |x
        xxxxx
        ---
    """)

    with pytest.raises(InvalidMapFileException):
        load_map_from_string(text)
