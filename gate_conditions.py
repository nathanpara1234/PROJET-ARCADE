from collections.abc import Iterator

type GateCondition = dict[str, str | list[GateCondition]]


def condition_is_true(condition: GateCondition, switch_states: dict[str, bool]) -> bool:
    condition_iterator: Iterator[str] = iter(condition)
    key = next(condition_iterator)
    value = condition.get(key)

    if key == "switch_is_on":
        if not isinstance(value, str):
            return False
        return switch_states.get(value, False)

    if key == "not":
        if not isinstance(value, list):
            return False
        return not condition_is_true(value[0], switch_states)

    if key == "and":
        if not isinstance(value, list):
            return False
        return condition_is_true(value[0], switch_states) and condition_is_true(value[1], switch_states)

    if key == "or":
        if not isinstance(value, list):
            return False
        return condition_is_true(value[0], switch_states) or condition_is_true(value[1], switch_states)

    return False
