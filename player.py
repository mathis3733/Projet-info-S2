import random
from position import Position


# classe pour representer un joueur
class Player:
    def __init__(self, name, color):
        self.name = name
        self.color = color

    def get_name(self):
        return self.name

    def get_color(self):
        return self.color

    # demande au joueur de saisir son coup
    def askMove(self):
        print("Entrez votre coup (ex: Pe2 Pe4) : ")
        coup = input()
        return coup


# AIPlayer herite de Player et joue de maniere intelligente
class AIPlayer(Player):
    def __init__(self, color):
        super().__init__("AI", color)

    def askMove(self, board, chess):
        colonnes = Position.get_colonnes()
        coups_possibles = []

        # on recupere tous les coups valides
        for p in board.get_pieces():
            if p.get_color() == self.color:
                for col in colonnes:
                    for row in range(1, 9):
                        pos_dest = Position(col, row)
                        if chess.isValidMove(p.get_position(), pos_dest):
                            coups_possibles.append((p.get_position(), pos_dest))

        if len(coups_possibles) == 0:
            return None

        # priorite 1 : est ce qu'on peut faire echec et mat ?
        for pos_orig, pos_dest in coups_possibles:
            board_sim = board.simuler_move(pos_orig, pos_dest)
            couleur_adverse = 1 - self.color
            coups_adversaire = []
            for p in board_sim.get_pieces():
                if p.get_color() == couleur_adverse:
                    for col in colonnes:
                        for row in range(1, 9):
                            pd = Position(col, row)
                            if p.isValidMove(pd, board_sim):
                                b2 = board_sim.simuler_move(p.get_position(), pd)
                                if not b2.est_en_echec(couleur_adverse):
                                    coups_adversaire.append(pd)
            if len(coups_adversaire) == 0 and board_sim.est_en_echec(couleur_adverse):
                return (pos_orig, pos_dest)

        # priorite 2 : manger une piece adverse
        valeurs = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 100}
        meilleur_coup = None
        meilleure_valeur = 0

        for pos_orig, pos_dest in coups_possibles:
            piece_cible = board.getPiece(pos_dest)
            if piece_cible != None and piece_cible.get_color() != self.color:
                valeur = valeurs.get(str(piece_cible), 0)
                if valeur > meilleure_valeur:
                    meilleure_valeur = valeur
                    meilleur_coup = (pos_orig, pos_dest)

        if meilleur_coup != None:
            return meilleur_coup

        # priorite 3 : eviter de se faire manger
        coups_sur = []
        couleur_adverse = 1 - self.color

        for pos_orig, pos_dest in coups_possibles:
            board_sim = board.simuler_move(pos_orig, pos_dest)
            en_danger = False
            for p_adverse in board_sim.get_pieces():
                if p_adverse.get_color() == couleur_adverse:
                    if p_adverse.isValidMove(pos_dest, board_sim):
                        en_danger = True
                        break
            if not en_danger:
                coups_sur.append((pos_orig, pos_dest))

        if len(coups_sur) > 0:
            return random.choice(coups_sur)

        # sinon coup aleatoire
        return random.choice(coups_possibles)
