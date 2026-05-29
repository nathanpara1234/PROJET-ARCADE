from collections.abc import Iterator

# type alias : une condition de porte est un dict avec une cle operateur et une valeur
type GateCondition = dict[str, str | list[GateCondition]]


def condition_is_true(condition: GateCondition, switch_states: dict[str, bool]) -> bool:
    # on prend le premier (et seul) opérateur du dictionnaire
    condition_iterator: Iterator[str] = iter(condition)
    key = next(condition_iterator)
    value = condition.get(key)

    if key == "switch_is_on":
        # vérifie si le switch est activé
        if not isinstance(value, str):
            return False
        return switch_states.get(value, False)

    if key == "not":
        # inverse le résultat
        if not isinstance(value, list):
            return False
        return not condition_is_true(value[0], switch_states)

    if key == "and":
        # AND : les deux conditions doivent être vraies
        if not isinstance(value, list):
            return False
        return condition_is_true(value[0], switch_states) and condition_is_true(value[1], switch_states)

    if key == "or":
        # OR : au moins une des deux doit être vraie
        if not isinstance(value, list):
            return False
        return condition_is_true(value[0], switch_states) or condition_is_true(value[1], switch_states)

    # si l'opérateur n'est pas reconnu on retourne False
    return False
