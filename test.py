if __name__ == '__main__':
    from pyYGO.enums import Phase, Player
    from pyYGO.duel import Duel
    from pyYGOAgent.ANN import _create_basic
    duel = Duel()
    print(_create_basic(duel))
    duel._turn_player = Player.OPPONENT
    duel._phase = Phase.END
    print(_create_basic(duel))