from collections.abc import Iterator


# Je definis le type d'une condition qui est un YAML recursif.
type GateCondition = dict[str, str | list[GateCondition]]


def condition_is_true(condition: GateCondition, switch_states: dict[str, bool]) -> bool:
    # Comme dans le cours, on cree d'abord un iterateur sur les cles.
    condition_iterator: Iterator[str] = iter(condition)
    key = next(condition_iterator)
    # Puis on recupere la valeur associee avec get()
    value = condition.get(key)

    if key == "switch_is_on":
        if not isinstance(value, str):
            return False
        return switch_states.get(value, False) # la valeur de l'état du switch est initialisé à False

    # evalue la sous-condition et inverse le resultat
    if key == "not":
        if not isinstance(value, list):
            return False
        return not condition_is_true(value[0], switch_states)

    # J'evalue les deux sous-conditions recursivement et je fais un "and".
    if key == "and":
        if not isinstance(value, list):
            return False
        return condition_is_true(value[0], switch_states) and condition_is_true(
            value[1], switch_states
        )

    # Meme chose, mais avec un "or"
    if key == "or":
        if not isinstance(value, list):
            return False
        return condition_is_true(value[0], switch_states) or condition_is_true(
            value[1], switch_states
        )

    return False
