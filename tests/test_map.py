from map import Map, GridCell #on va utiliser des choses qui sont dans le fichier map.py
#map la classe qui represente une carte
#gridcell le type qui represente ce qu'il y a dans une case


def test_get() -> None:
    grid = [
        [GridCell.GRASS, GridCell.BUSH],
        [GridCell.CRYSTAL, GridCell.GRASS],
    ]

    m = Map( #on créer une map 2x2
        width=2,
        height=2,
        player_start_x=0,
        player_start_y=0,
        _grid=grid
    )

    assert m.width == 2
    assert m.height == 2
    assert m.get(0, 0) == GridCell.GRASS #qu’est-ce qu’il y a à la position (0,0) ?
    assert m.get(1, 0) == GridCell.BUSH#meme chose on verifie si il y a bien un buisson en (1,0)
    assert m.get(0, 1) == GridCell.CRYSTAL#idem avec diamand en (0,1)


def test_size()-> None:

    grid = [
        [GridCell.GRASS] #on crée une grille 1x1 avec que une case qui est GRASS
    ]

    m = Map(1, 1, 0, 0, grid)# on créer une map de largeur et de longueur 1

    assert m.width == 1# on verifie que la taille de la map est correcte
    assert m.height == 1

def test_error()-> None: # fonction qui test le lancage d'une erreur lorsqu'on sort de la map

    grid = [[GridCell.GRASS]]

    m = Map(1,1,0,0,grid)

    try:
        m.get(-1,0) #on teste une position invalide
    except IndexError:
        return

    assert False
