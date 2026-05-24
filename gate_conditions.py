#Je définis le type d'une condition qui est un YAML récursif

type GateCondition = dict[str, str | list[GateCondition]]

def condition_is_true(condition: GateCondition, switch_states: dict[str, bool]) -> bool:# Calcule si une condition de portail est vraie.
    # tout d'abord je récupere la seule clé de la condition
    key = next(iter(condition))
    value = condition[key]

    if key == "switch_is_on":
        if not isinstance(value, str):
            return False
        return switch_states[value]
    # j'évalue la sous condition et j'inverse le resultat
    if key == "not":
        if not isinstance(value, list):
            return False
        return not condition_is_true(value[0], switch_states)
    # j'évalue les deux sous conditions récursivement et je fais un "and"
    if key == "and":
        if not isinstance(value, list):
            return False
        return ((condition_is_true(value[0], switch_states))and (condition_is_true(value[1], switch_states)))
    # meme chose mais je fais un or à la fin
    if key == "or":
        if not isinstance(value, list):
            return False
        return ((condition_is_true(value[0], switch_states))or (condition_is_true(value[1], switch_states)))

    return False
